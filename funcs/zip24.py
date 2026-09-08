K = 10**18

def _insert_order(addr, pair, order_type, order_start, order_new, quote_value, base_value):
    assert order_type in ['buy', 'sell']
    order_id = order_start
    while True:
        order, _ = get('predict', f'{pair}_{order_type}', None, str(order_id))
        price = - quote_value * K // base_value

        if order is None:
            put(addr, 'predict', f'{pair}_{order_type}',
                [addr, base_value, quote_value, price, None, None], str(order_new))
            order_new += 1
            put(addr, 'predict', f'{pair}_{order_type}_new', order_new)
            break

        if order_type == 'buy':
            cond = price > order[3]
        else:
            cond = price < order[3]

        if cond:
            next_order_id = order[5]
            put(addr, 'predict', f'{pair}_{order_type}',
                [addr, base_value, quote_value, price, order_id, next_order_id], str(order_new))
            if next_order_id is None:
                order_start = order_new
                put(addr, 'predict', f'{pair}_{order_type}_start', order_new)
            order[5] = order_new
            order_new += 1
            put(addr, 'predict', f'{pair}_{order_type}_new', order_new)

            put(addr, 'predict', f'{pair}_{order_type}', order, str(order_id))
            if next_order_id is not None:
                next_order, _ = get('predict', f'{pair}_{order_type}', None, str(next_order_id))
                if next_order is not None:
                    next_order[4] = order[5]
                    put(addr, 'predict', f'{pair}_{order_type}', next_order, str(next_order_id))
            break

        if order[4] is None:
            put(addr, 'predict', f'{pair}_{order_type}',
                [addr, base_value, quote_value, price, None, order_id], str(order_new))
            put(addr, 'predict', f'{pair}_{order_type}',
                [order[0], order[1], order[2], order[3], order_new, order[5]], str(order_id))
            order_new += 1
            put(addr, 'predict', f'{pair}_{order_type}_new', order_new)
            break

        order_id = order[4]
    return order_start, order_new

def _remove_order(addr, pair, order, order_start, buy_or_sell):
    assert buy_or_sell in ['buy', 'sell']
    if order[4]:
        prev_order, _ = get('predict', f'{pair}_{buy_or_sell}', None, str(order[4]))
        prev_order[5] = order[5]
        put(prev_order[0], 'predict', f'{pair}_{buy_or_sell}', prev_order, str(order[4]))

    if order[5]:
        next_order, _ = get('predict', f'{pair}_{buy_or_sell}', None, str(order[5]))
        next_order[4] = order[4]
        put(next_order[0], 'predict', f'{pair}_{buy_or_sell}', next_order, str(order[5]))

    if order[4] is not None and order[5] is None:
        order_start = order[4]
        put(addr, 'predict', f'{pair}_{buy_or_sell}_start', order_start)

    elif order[4] is None and order[5] is None:
        order_new, _ = get('predict', f'{pair}_{buy_or_sell}_new', 1)
        order_start = order_new
        put(addr, 'predict', f'{pair}_{buy_or_sell}_start', order_start)

    return order_start

def _update_slug_balance(addr, slug, tick, delta):
    prev, manager = get('predict', f'{slug}_{tick}_balance_new', None)
    balance_tuple, _ = get('predict', f'{slug}_{tick}_balance', None, addr)
    if balance_tuple is None:
        balance = 0
        put(manager, 'predict', f'{slug}_{tick}_balance_new', addr)
    else:
        balance = balance_tuple[0]
        prev = balance_tuple[1]
    balance += delta
    assert balance >= 0
    put(addr, 'predict', f'{slug}_{tick}_balance', [balance, prev], addr)

def _update_quote_balance(addr, quote_tick, delta):
    balance, _ = get(quote_tick, 'balance', 0, addr)
    balance += delta
    assert balance >= 0
    put(addr, quote_tick, 'balance', balance, addr)


def predict_limit_order(info, args):
    assert args['f'] == 'predict_limit_order'
    sender = info['sender']
    addr = handle_lookup(sender)

    slug = args['a'][0]
    yes_or_no = args['a'][2]
    assert set(slug) <= set(string.ascii_lowercase+string.digits+'_')
    assert yes_or_no in set(['yes', 'no'])

    pair = f'{slug}_{yes_or_no}'
    base_value = int(args['a'][1])
    quote_value = int(args['a'][3])
    assert base_value * quote_value < 0

    quote_tick, _ = get('predict', f'{slug}_quote_token', None)
    assert quote_tick, "Slug not exists"

    predict_buy_start, _ = get('predict', f'{pair}_buy_start', 1)
    predict_buy_new, _ = get('predict', f'{pair}_buy_new', 1)
    predict_sell_start, _ = get('predict', f'{pair}_sell_start', 1)
    predict_sell_new, _ = get('predict', f'{pair}_sell_new', 1)

    if base_value < 0 and quote_value > 0:
        buy_or_sell = 'sell'
        _update_slug_balance(addr, slug, yes_or_no, base_value)
        make_base = - base_value

        order_id = predict_sell_new
        predict_sell_start, predict_sell_new = _insert_order(addr, pair, 'sell', predict_sell_start, predict_sell_new, quote_value, base_value)

    elif base_value > 0 and quote_value < 0:
        buy_or_sell = 'buy'
        _update_quote_balance(addr, quote_tick, quote_value)
        make_base = base_value

        order_id = predict_buy_new
        predict_buy_start, predict_buy_new = _insert_order(addr, pair, 'buy', predict_buy_start, predict_buy_new, quote_value, base_value)

    predict_sell_id = predict_sell_start
    highest_buy_price = None

    take_base = 0
    take_quote = 0
    while True:
        sell, _ = get('predict', f'{pair}_sell', None, str(predict_sell_id))
        if not sell:
            break
        sell_price = sell[3]
        if highest_buy_price and sell_price > highest_buy_price:
            break

        predict_buy_id = predict_buy_start
        while True:
            buy, _ = get('predict', f'{pair}_buy', None, str(predict_buy_id))
            if not buy:
                break
            buy_price = buy[3]
            if highest_buy_price is None:
                highest_buy_price = buy_price
            if sell_price > buy_price:
                predict_buy_id = buy[4]
                continue

            matched_price = sell_price
            dx_base = min(-sell[1], buy[1])
            dx_quote = dx_base * matched_price // K
            sell[1] += dx_base
            sell[2] -= dx_quote
            buy[1] -= dx_base
            buy[2] += dx_quote
            take_base += dx_base
            take_quote += dx_quote

            _update_slug_balance(buy[0], slug, yes_or_no, dx_base)
            _update_quote_balance(sell[0], quote_tick, dx_quote)
            if buy[1] == 0:
                predict_buy_start = _remove_order(addr, pair, buy, predict_buy_start, 'buy')

                if buy[2] < 0:
                    _update_quote_balance(buy[0], quote_tick, -buy[2])

                put(buy[0], 'predict', f'{pair}_buy', None, str(predict_buy_id))
            else:
                put(buy[0], 'predict', f'{pair}_buy', buy, str(predict_buy_id))

            if sell[1] == 0:
                break
            if buy[4] is None:
                break
            predict_buy_id = buy[4]

        if sell[1] == 0:
            predict_sell_start = _remove_order(addr, pair, sell, predict_sell_start, 'sell')

            if sell[1] < 0:
                _update_slug_balance(sell[0], slug, yes_or_no, -sell[1])

            put(sell[0], 'predict', f'{pair}_sell', None, str(predict_sell_id))
        else:
            put(sell[0], 'predict', f'{pair}_sell', sell, str(predict_sell_id))

        if sell[4] is None:
            break
        predict_sell_id = sell[4]

    make_base -= take_base
    assert make_base >= 0
    make_price = - quote_value * K // base_value
    event('PredictLimitMake', [pair, buy_or_sell, addr, make_base, make_price, order_id])
    if take_base > 0:
        take_price = take_quote * K // take_base
        event('PredictLimitTake', [pair, buy_or_sell, addr, take_base, take_price, order_id])


def predict_market_order(info, args):
    assert args['f'] == 'predict_market_order'
    sender = info['sender']
    addr = handle_lookup(sender)

    slug = args['a'][0]
    yes_or_no = args['a'][2]
    assert set(slug) <= set(string.ascii_lowercase+string.digits+'_')
    assert yes_or_no in set(['yes', 'no'])

    quote_tick, _ = get('predict', f'{slug}_quote_token', None)
    assert quote_tick, "Slug not exists"
    pair = f'{slug}_{yes_or_no}'

    base_value = args['a'][1]
    quote_value = args['a'][3]
    predict_sell_start, _ = get('predict', f'{pair}_sell_start', 1)
    predict_buy_start, _ = get('predict', f'{pair}_buy_start', 1)

    take_base = 0
    take_quote = 0
    if quote_value is None and int(base_value) < 0:
        buy_or_sell = 'sell'
        base_value = int(args['a'][1])
        [base_balance, _], _ = get('predict', f'{pair}_balance', [0, None], addr)

        predict_buy_id = predict_buy_start
        while True:
            buy, _ = get('predict', f'{pair}_buy', None, str(predict_buy_id))
            if buy is None:
                break

            price = buy[3]
            dx_base = min(buy[1], -buy[2] * K // price, -base_value)
            dx_quote = dx_base * price // K
            if dx_base == 0 or dx_quote == 0:
                break
            if base_balance - dx_base < 0:
                break
            buy[1] -= dx_base
            buy[2] += dx_quote
            take_base += dx_base
            take_quote += dx_quote
            base_balance -= dx_base

            if buy[1] == 0 or buy[1] // price == 0:
                predict_buy_start = _remove_order(addr, pair, buy, predict_buy_start, 'buy')
                if buy[2] < 0:
                    _update_quote_balance(buy[0], quote_tick, -buy[2])

                put(buy[0], 'predict', f'{pair}_buy', None, str(predict_buy_id))
            else:
                put(buy[0], 'predict', f'{pair}_buy', buy, str(predict_buy_id))

            _update_slug_balance(buy[0], slug, yes_or_no, dx_base)
            base_value += dx_base
            assert base_value <= 0
            _update_quote_balance(addr, quote_tick, dx_quote)
            if buy[4] is None:
                break
            predict_buy_id = buy[4]

        _update_slug_balance(addr, slug, yes_or_no, -take_base)

    elif quote_value is None and int(base_value) > 0:
        buy_or_sell = 'buy'
        base_value = int(args['a'][1])
        quote_balance, _ = get(quote_tick, 'balance', 0, addr)

        predict_sell_id = predict_sell_start
        while True:
            sell, _ = get('predict', f'{pair}_sell', None, str(predict_sell_id))
            if sell is None:
                break

            price = sell[3]
            dx_base = min(-sell[1], quote_balance * K // price, base_value)
            dx_quote = dx_base * price // K
            if dx_base == 0 or dx_quote == 0:
                break
            if quote_balance - dx_quote < 0:
                break

            sell[1] += dx_base
            sell[2] -= dx_quote
            take_base += dx_base
            take_quote += dx_quote
            quote_balance -= dx_quote

            if sell[1] == 0 or sell[1] // price == 0:
                predict_sell_start = _remove_order(addr, pair, sell, predict_sell_start, 'sell')
                if sell[1] < 0:
                    _update_slug_balance(sell[0], slug, yes_or_no, -sell[1])

                put(sell[0], 'predict', f'{pair}_sell', None, str(predict_sell_id))
            else:
                put(sell[0], 'predict', f'{pair}_sell', sell, str(predict_sell_id))

            _update_quote_balance(sell[0], quote_tick, dx_quote)
            base_value -= dx_base
            assert base_value >= 0
            _update_slug_balance(addr, slug, yes_or_no, dx_base)
            if sell[4] is None:
                break
            predict_sell_id = sell[4]

        _update_quote_balance(addr, quote_tick, -take_quote)

    elif base_value is None and int(quote_value) < 0:
        buy_or_sell = 'buy'
        quote_value = int(args['a'][3])
        quote_balance, _ = get(quote_tick, 'balance', 0, addr)

        predict_sell_id = predict_sell_start
        while True:
            sell, _ = get('predict', f'{pair}_sell', None, str(predict_sell_id))
            if sell is None:
                break

            price = sell[3]
            dx_base = min(-sell[1], -quote_value * K // price)
            dx_quote = dx_base * price // K
            if dx_base == 0 or  dx_quote == 0:
                break
            if quote_balance - dx_quote < 0:
                break

            sell[1] += dx_base
            sell[2] -= dx_quote
            take_base += dx_base
            take_quote += dx_quote
            quote_balance -= dx_quote

            if sell[1] == 0 or sell[1] // price == 0:
                predict_sell_start = _remove_order(addr, pair, sell, predict_sell_start, 'sell')
                if sell[1] < 0:
                    _update_slug_balance(sell[0], slug, yes_or_no, -sell[1])

                put(sell[0], 'predict', f'{pair}_sell', None, str(predict_sell_id))
            else:
                put(sell[0], 'predict', f'{pair}_sell', sell, str(predict_sell_id))

            _update_quote_balance(sell[0], quote_tick, dx_quote)
            quote_value += dx_quote
            assert quote_value <= 0
            _update_slug_balance(addr, slug, yes_or_no, dx_base)
            if sell[4] is None:
                break
            predict_sell_id = sell[4]

        _update_quote_balance(addr, quote_tick, -take_quote)

    elif base_value is None and int(quote_value) > 0:
        buy_or_sell = 'sell'
        quote_value = int(args['a'][3])
        [base_balance, _], _ = get('predict', f'{pair}_balance', [0, None], addr)

        predict_buy_id = predict_buy_start
        while True:
            buy, _ = get('predict', f'{pair}_buy', None, str(predict_buy_id))
            if buy is None:
                break

            price = buy[3]
            dx_base = min(buy[1], base_balance, quote_value * K // price)
            dx_quote = dx_base * price // K
            if dx_base == 0 or dx_quote == 0:
                break
            if base_balance - dx_base < 0:
                break

            buy[1] -= dx_base
            buy[2] += dx_quote
            take_base += dx_base
            take_quote += dx_quote
            base_balance -= dx_base

            if buy[1] == 0 or buy[1] // price == 0:
                predict_buy_start = _remove_order(addr, pair, buy, predict_buy_start, 'buy')
                if buy[2] < 0:
                    _update_quote_balance(buy[0], quote_tick, -buy[2])

                put(buy[0], 'predict', f'{pair}_buy', None, str(predict_buy_id))
            else:
                put(buy[0], 'predict', f'{pair}_buy', buy, str(predict_buy_id))

            _update_slug_balance(buy[0], slug, yes_or_no, dx_base)
            quote_value -= dx_quote
            assert quote_value >= 0
            _update_quote_balance(addr, quote_tick, dx_quote)
            if buy[4] is None:
                break
            predict_buy_id = buy[4]

        _update_slug_balance(addr, slug, yes_or_no, -take_base)

    if take_base > 0:
        price = take_quote * K // take_base
        event('PredictMarketTake', [pair, buy_or_sell, addr, take_base, price])


def predict_limit_order_cancel(info, args):
    assert args['f'] == 'predict_limit_order_cancel'
    sender = info['sender']
    addr = handle_lookup(sender)

    slug = args['a'][0]
    yes_or_no = args['a'][1]
    buy_or_sell = args['a'][2]
    predict_order_id = int(args['a'][3])
    assert set(slug) <= set(string.ascii_lowercase+string.digits+'_')
    assert yes_or_no in set(['yes', 'no'])
    assert buy_or_sell in ['buy', 'sell']
    assert predict_order_id > 0

    pair = f'{slug}_{yes_or_no}'
    order_key = f'{pair}_{buy_or_sell}'
    quote_tick, _ = get('predict', f'{slug}_quote_token', None)
    order, _ = get('predict', order_key, None, str(predict_order_id))

    if order is None:
        return

    assert order[0] == addr, "Sender is not the owner of the order"
    prev_order_id = order[4]
    next_order_id = order[5]

    if prev_order_id is not None:
        prev_order, _ = get('predict', order_key, None, str(prev_order_id))
        if prev_order:
            prev_order[5] = next_order_id
            put(prev_order[0], 'predict', order_key, prev_order, str(prev_order_id))

    if next_order_id is not None:
        next_order, _ = get('predict', order_key, None, str(next_order_id))
        if next_order:
            next_order[4] = prev_order_id
            put(next_order[0], 'predict', order_key, next_order, str(next_order_id))

    start_key = f'{pair}_{buy_or_sell}_start'
    current_start, _ = get('predict', start_key, 1)
    if current_start == predict_order_id:
        if prev_order_id is not None:
            put(addr, 'predict', start_key, prev_order_id)
        else:
            new_start_key = f'{pair}_{buy_or_sell}_new'
            new_start_val, _ = get('predict', new_start_key, 1)
            put(addr, 'predict', start_key, new_start_val)

    if buy_or_sell == 'sell':
        if order[1] < 0:
            _update_slug_balance(addr, slug, yes_or_no, -order[1])
    elif buy_or_sell == 'buy':
        if order[2] < 0:
            _update_quote_balance(addr, quote_tick, -order[2])

    put(addr, 'predict', order_key, None, str(predict_order_id))
    event('PredictOrderCancel', [predict_order_id, buy_or_sell, pair])


def predict_create(info, args):
    assert args['f'] == 'predict_create'
    sender = info['sender']
    addr = handle_lookup(sender)

    slug = args['a'][0]
    quote_tick = args['a'][1]
    assert set(slug) <= set(string.ascii_lowercase+string.digits+'_')

    quote_tokens, _ = get('predict', 'quote_tokens', [])
    assert quote_tick in quote_tokens, f'{quote_tick} is not a designated quote token'

    manager, _ = get('predict', 'manager', None)
    assert manager == addr, f"Sender must be the owner of predict system"
    created, _ = get('predict', f'{slug}_quote_token', None)
    assert created is None, "Slug already exists"
    put(addr, 'predict', f'{slug}_quote_token', quote_tick)

    put(addr, 'predict', f'{slug}_yes_buy_start', 1)
    put(addr, 'predict', f'{slug}_yes_buy_new', 1)
    put(addr, 'predict', f'{slug}_yes_sell_start', 1)
    put(addr, 'predict', f'{slug}_yes_sell_new', 1)
    put(addr, 'predict', f'{slug}_yes_balance_new', None)

    put(addr, 'predict', f'{slug}_no_buy_start', 1)
    put(addr, 'predict', f'{slug}_no_buy_new', 1)
    put(addr, 'predict', f'{slug}_no_sell_start', 1)
    put(addr, 'predict', f'{slug}_no_sell_new', 1)
    put(addr, 'predict', f'{slug}_no_balance_new', None)


def predict_mint(info, args):
    assert args['f'] == 'predict_mint'
    sender = info['sender']
    addr = handle_lookup(sender)

    slug = args['a'][0]
    assert set(slug) <= set(string.ascii_lowercase+string.digits+'_')

    quote_tick, _ = get('predict', f'{slug}_quote_token', None)
    assert quote_tick, "Slug is not created"

    quote_value = int(args['a'][1])
    assert quote_value > 0

    _update_quote_balance(addr, quote_tick, -quote_value)

    #TODO: move the balance to the predict slug

    for tick in ['yes', 'no']:
        _update_slug_balance(addr, slug, tick, quote_value)

    #TODO: add event


def predict_submit(info, args):
    assert args['f'] == 'predict_submit'
    sender = info['sender']
    addr = handle_lookup(sender)

    slug = args['a'][0]
    yes_or_no = args['a'][1]
    assert set(slug) <= set(string.ascii_lowercase+string.digits+'_')
    assert yes_or_no in set(['yes', 'no'])
    lose_tick = 'no' if yes_or_no == 'yes' else 'yes'

    quote_tick, _ = get('predict', f'{slug}_quote_token', None)
    assert quote_tick, "Slug not exists"

    win_pair = f'{slug}_{yes_or_no}'
    win_sell_start, _ = get('predict', f'{win_pair}_sell_start', 1)
    win_buy_start, _ = get('predict', f'{win_pair}_buy_start', 1)

    predict_sell_id = win_sell_start
    while True:
        sell, _ = get('predict', f'{win_pair}_sell', None, str(predict_sell_id))
        if not sell:
            break
        next_id = sell[4]
        if sell[1] < 0:
            _update_slug_balance(sell[0], slug, yes_or_no, -sell[1])
        put(sell[0], 'predict', f'{win_pair}_sell', None, str(predict_sell_id))
        if next_id is None:
            break
        predict_sell_id = next_id

    predict_buy_id = win_buy_start
    while True:
        buy, _ = get('predict', f'{win_pair}_buy', None, str(predict_buy_id))
        if not buy:
            break
        next_id = buy[4]
        if buy[2] < 0:
            _update_quote_balance(buy[0], quote_tick, -buy[2])
        put(buy[0], 'predict', f'{win_pair}_buy', None, str(predict_buy_id))
        if next_id is None:
            break
        predict_buy_id = next_id

    put(addr, 'predict', f'{win_pair}_sell_start', None)
    put(addr, 'predict', f'{win_pair}_sell_new', None)
    put(addr, 'predict', f'{win_pair}_buy_start', None)
    put(addr, 'predict', f'{win_pair}_buy_new', None)

    win_balance_new, _ = get('predict', f'{win_pair}_balance_new', None)
    current_addr = win_balance_new
    while current_addr is not None:
        balance_tuple, _ = get('predict', f'{win_pair}_balance', None, current_addr)
        if balance_tuple is None:
            break
        balance, prev = balance_tuple
        assert balance >= 0
        _update_quote_balance(current_addr, quote_tick, balance)
        put(current_addr, 'predict', f'{win_pair}_balance', None, current_addr)
        current_addr = prev
    put(addr, 'predict', f'{win_pair}_balance_new', None)

    lose_pair = f'{slug}_{lose_tick}'
    lose_sell_start, _ = get('predict', f'{lose_pair}_sell_start', 1)
    lose_buy_start, _ = get('predict', f'{lose_pair}_buy_start', 1)

    predict_sell_id = lose_sell_start
    while True:
        sell, _ = get('predict', f'{lose_pair}_sell', None, str(predict_sell_id))
        if not sell:
            break
        next_id = sell[4]
        put(sell[0], 'predict', f'{lose_pair}_sell', None, str(predict_sell_id))
        if next_id is None:
            break
        predict_sell_id = next_id

    predict_buy_id = lose_buy_start
    while True:
        buy, _ = get('predict', f'{lose_pair}_buy', None, str(predict_buy_id))
        if not buy:
            break
        next_id = buy[4]
        put(buy[0], 'predict', f'{lose_pair}_buy', None, str(predict_buy_id))
        if next_id is None:
            break
        predict_buy_id = next_id

    put(addr, 'predict', f'{lose_pair}_sell_start', None)
    put(addr, 'predict', f'{lose_pair}_sell_new', None)
    put(addr, 'predict', f'{lose_pair}_buy_start', None)
    put(addr, 'predict', f'{lose_pair}_buy_new', None)

    balance_new, _ = get('predict', f'{lose_pair}_balance_new', None)
    current_addr = balance_new
    while current_addr is not None:
        balance_tuple, _ = get('predict', f'{lose_pair}_balance', None, current_addr)
        if balance_tuple is None:
            break
        _, prev = balance_tuple
        put(current_addr, 'predict', f'{lose_pair}_balance', None, current_addr)
        current_addr = prev
    put(addr, 'predict', f'{lose_pair}_balance_new', None)

    put(addr, 'predict', f'{slug}_quote_token', None)
    event('PredictSubmit', [slug, yes_or_no])


def predict_set_quote_token(info, args):
    assert args['f'] == 'predict_set_quote_token'
    sender = info['sender']
    addr = handle_lookup(sender)

    manager, _ = get('predict', 'manager', None)
    assert manager is not None, "Manager not set"
    assert addr == manager, "Only the manager can add quote tokens"

    new_tokens = args['a'][0]
    assert isinstance(new_tokens, list), "Quote tokens must be a list"

    quote_tokens, _ = get('predict', 'quote_tokens', [])

    for token in new_tokens:
        assert isinstance(token, str), "Token ticker must be a string"
        assert set(token) <= set(string.ascii_uppercase+'_'), "Invalid characters in token ticker"
        if token not in quote_tokens:
            quote_tokens.append(token)

    put(addr, 'predict', 'quote_tokens', quote_tokens)


def predict_vote_manager(info, args):
    assert args['f'] == 'predict_vote_manager'
    sender = info['sender']
    addr = handle_lookup(sender)

    committee_members, _ = get('committee', 'members', [])
    committee_members = set(committee_members)
    assert addr in committee_members, "Only committee members can vote"

    user = args['a'][0]
    assert isinstance(user, str), "User address must be a string"

    proposal_key = f'predict_manager:{user}'
    votes, _ = get('committee', 'proposal', [], proposal_key)
    votes = set(votes)
    votes.add(addr)

    if len(votes) >= len(committee_members) * 2 // 3:
        put(addr, 'predict', 'manager', user)
        put(addr, 'committee', 'proposal', [], proposal_key)
    else:
        put(addr, 'committee', 'proposal', list(votes), proposal_key)
