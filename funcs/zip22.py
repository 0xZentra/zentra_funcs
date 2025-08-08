K = 10**18

def _insert_order(addr, pair, order_type, order_start, order_new, quote_value, base_value):
    assert order_type in ['buy', 'sell']
    order_id = order_start
    while True:
        order, _ = get('trade', f'{pair}_{order_type}', None, str(order_id))
        price = - quote_value * K // base_value

        if order is None:
            put(addr, 'trade', f'{pair}_{order_type}',
                [addr, base_value, quote_value, price, None, None], str(order_new))
            order_new += 1
            put(addr, 'trade', f'{pair}_{order_type}_new', order_new)
            break

        if order_type == 'buy':
            cond = price > order[3]
        else:
            cond = price < order[3]

        if cond:
            next_order_id = order[5]
            put(addr, 'trade', f'{pair}_{order_type}',
                [addr, base_value, quote_value, price, order_id, next_order_id], str(order_new))
            if next_order_id is None:
                order_start = order_new
                put(addr, 'trade', f'{pair}_{order_type}_start', order_new)
            order[5] = order_new
            order_new += 1
            put(addr, 'trade', f'{pair}_{order_type}_new', order_new)

            put(addr, 'trade', f'{pair}_{order_type}', order, str(order_id))
            if next_order_id is not None:
                next_order, _ = get('trade', f'{pair}_{order_type}', None, str(next_order_id))
                if next_order is not None:
                    next_order[4] = order[5]
                    put(addr, 'trade', f'{pair}_{order_type}', next_order, str(next_order_id))
            break

        if order[4] is None:
            put(addr, 'trade', f'{pair}_{order_type}',
                [addr, base_value, quote_value, price, None, order_id], str(order_new))
            put(addr, 'trade', f'{pair}_{order_type}',
                [order[0], order[1], order[2], order[3], order_new, order[5]], str(order_id))
            order_new += 1
            put(addr, 'trade', f'{pair}_{order_type}_new', order_new)
            break

        order_id = order[4]
    return order_start, order_new


def _remove_order(addr, pair, order, order_start, buy_or_sell):
    assert buy_or_sell in ['buy', 'sell']
    if order[4]:
        prev_order, _ = get('trade', f'{pair}_{buy_or_sell}', None, str(order[4]))
        prev_order[5] = order[5]
        put(prev_order[0], 'trade', f'{pair}_{buy_or_sell}', prev_order, str(order[4]))

    if order[5]:
        next_order, _ = get('trade', f'{pair}_{buy_or_sell}', None, str(order[5]))
        next_order[4] = order[4]
        put(next_order[0], 'trade', f'{pair}_{buy_or_sell}', next_order, str(order[5]))

    if order[4] is not None and order[5] is None:
        order_start = order[4]
        put(addr, 'trade', f'{pair}_{buy_or_sell}_start', order_start)

    elif order[4] is None and order[5] is None:
        order_new, _ = get('trade', f'{pair}_{buy_or_sell}_new', 1)
        order_start = order_new
        put(addr, 'trade', f'{pair}_{buy_or_sell}_start', order_start)

    return order_start


def trade_limit_order(info, args):
    assert args['f'] == 'trade_limit_order'
    sender = info['sender']
    addr = handle_lookup(sender)

    base_tick = args['a'][0]
    quote_tick = args['a'][2]
    assert set(base_tick) <= set(string.ascii_uppercase+'_')
    assert set(quote_tick) <= set(string.ascii_uppercase+'_')

    pair = '%s_%s' % tuple([base_tick, quote_tick])
    base_value = int(args['a'][1])
    quote_value = int(args['a'][3])
    assert base_value * quote_value < 0

    trade_buy_start, _ = get('trade', f'{pair}_buy_start', 1)
    trade_buy_new, _ = get('trade', f'{pair}_buy_new', 1)
    trade_sell_start, _ = get('trade', f'{pair}_sell_start', 1)
    trade_sell_new, _ = get('trade', f'{pair}_sell_new', 1)

    if base_value < 0 and quote_value > 0:
        buy_or_sell = 'sell'
        balance, _ = get(base_tick, 'balance', 0, addr)
        balance += base_value
        make_amount = - base_value
        assert balance >= 0
        put(addr, base_tick, 'balance', balance, addr)

        order_id = trade_sell_new
        trade_sell_start, trade_sell_new = _insert_order(addr, pair, 'sell', trade_sell_start, trade_sell_new, quote_value, base_value)

    elif base_value > 0 and quote_value < 0:
        buy_or_sell = 'buy'
        balance, _ = get(quote_tick, 'balance', 0, addr)
        balance += quote_value
        make_amount = - quote_value
        assert balance >= 0
        put(addr, quote_tick, 'balance', balance, addr)

        order_id = trade_buy_new
        trade_buy_start, trade_buy_new = _insert_order(addr, pair, 'buy', trade_buy_start, trade_buy_new, quote_value, base_value)

    trade_sell_id = trade_sell_start
    highest_buy_price = None
    take_amount = 0

    while True:
        sell, _ = get('trade', f'{pair}_sell', None, str(trade_sell_id))
        if not sell:
            break
        sell_price = sell[3]
        if highest_buy_price and sell_price > highest_buy_price:
            break

        trade_buy_id = trade_buy_start
        while True:
            buy, _ = get('trade', f'{pair}_buy', None, str(trade_buy_id))
            if not buy:
                break
            buy_price = buy[3]
            if highest_buy_price is None:
                highest_buy_price = buy_price
            if sell_price > buy_price:
                trade_buy_id = buy[4]
                continue

            matched_price = sell_price
            dx_base = min(-sell[1], buy[1])
            dx_quote = dx_base * matched_price // K
            sell[1] += dx_base
            sell[2] -= dx_quote
            buy[1] -= dx_base
            buy[2] += dx_quote
            if buy_or_sell == 'buy':
                take_amount += dx_base
            else:
                take_amount += dx_quote
            balance, _ = get(base_tick, 'balance', 0, buy[0])
            balance += dx_base
            assert balance >= 0
            put(buy[0], base_tick, 'balance', balance, buy[0])

            balance, _ = get(quote_tick, 'balance', 0, sell[0])
            balance += dx_quote
            assert balance >= 0
            put(sell[0], quote_tick, 'balance', balance, sell[0])

            if buy[1] == 0:
                trade_buy_start = _remove_order(addr, pair, buy, trade_buy_start, 'buy')

                if buy[2] < 0:
                    balance, _ = get(quote_tick, 'balance', 0, buy[0])
                    balance -= buy[2]
                    assert balance >= 0
                    put(buy[0], quote_tick, 'balance', balance, buy[0])
    
                put(buy[0], 'trade', f'{pair}_buy', None, str(trade_buy_id))
            else:
                put(buy[0], 'trade', f'{pair}_buy', buy, str(trade_buy_id))

            if sell[1] == 0:
                break
            if buy[4] is None:
                break
            trade_buy_id = buy[4]

        if sell[1] == 0:
            trade_sell_start = _remove_order(addr, pair, sell, trade_sell_start, 'sell')

            if sell[1] < 0:
                balance, _ = get(base_tick, 'balance', 0, sell[0])
                balance -= sell[1]
                assert balance >= 0
                put(sell[0], base_tick, 'balance', balance, sell[0])

            put(sell[0], 'trade', f'{pair}_sell', None, str(trade_sell_id))
        else:
            put(sell[0], 'trade', f'{pair}_sell', sell, str(trade_sell_id))

        if sell[4] is None:
            break
        trade_sell_id = sell[4]

    make_amount -= take_amount
    assert make_amount >= 0
    price = 0
    event('TradeOrderMake', [pair, buy_or_sell, addr, make_amount, price, order_id])
    if take_amount > 0:
        cost = 0
        event('TradeOrderTake', [pair, buy_or_sell, addr, take_amount, price, cost])


def trade_market_order(info, args):
    assert args['f'] == 'trade_market_order'
    sender = info['sender']
    addr = handle_lookup(sender)

    base_tick = args['a'][0]
    quote_tick = args['a'][2]
    assert set(base_tick) <= set(string.ascii_uppercase+'_')
    assert set(quote_tick) <= set(string.ascii_uppercase+'_')
    pair = '%s_%s' % tuple([base_tick, quote_tick])

    base_value = args['a'][1]
    quote_value = args['a'][3]
    trade_sell_start, _ = get('trade', f'{pair}_sell_start', 1)
    trade_buy_start, _ = get('trade', f'{pair}_buy_start', 1)

    take_amount = 0
    if quote_value is None and int(base_value) < 0:
        buy_or_sell = 'sell'
        base_value = int(args['a'][1])
        base_balance, _ = get(base_tick, 'balance', 0, addr)
        base_sum = 0

        trade_buy_id = trade_buy_start
        while True:
            buy, _ = get('trade', f'{pair}_buy', None, str(trade_buy_id))
            if buy is None:
                break

            price = buy[3]
            dx_base = min(buy[1], -buy[2] * K // price, -base_value)
            dx_quote = dx_base * price // K
            if dx_base == 0 or dx_quote == 0:
                break
            buy[1] -= dx_base
            buy[2] += dx_quote
            take_amount += dx_quote

            if base_balance - dx_base < 0:
                break
            base_balance -= dx_base
            base_sum += dx_base

            if buy[1] == 0 or buy[1] // price == 0:
                trade_buy_start = _remove_order(addr, pair, buy, trade_buy_start, 'buy')

                if buy[2] < 0:
                    balance, _ = get(quote_tick, 'balance', 0, buy[0])
                    balance -= buy[2]
                    assert balance >= 0
                    put(buy[0], quote_tick, 'balance', balance, buy[0])
    
                put(buy[0], 'trade', f'{pair}_buy', None, str(trade_buy_id))
            else:
                put(buy[0], 'trade', f'{pair}_buy', buy, str(trade_buy_id))

            balance, _ = get(base_tick, 'balance', 0, buy[0])
            balance += dx_base
            assert balance >= 0
            put(addr, base_tick, 'balance', balance, buy[0])

            base_value += dx_base
            assert base_value <= 0
            balance, _ = get(quote_tick, 'balance', 0, addr)
            balance += dx_quote
            assert balance >= 0
            put(addr, quote_tick, 'balance', balance, addr)

            if buy[4] is None:
                break
            trade_buy_id = buy[4]

        balance, _ = get(base_tick, 'balance', 0, addr)
        balance -= base_sum
        assert balance >= 0
        put(addr, base_tick, 'balance', balance, addr)

    elif quote_value is None and int(base_value) > 0:
        buy_or_sell = 'buy'
        base_value = int(args['a'][1])
        quote_balance, _ = get(quote_tick, 'balance', 0, addr)
        quote_sum = 0

        trade_sell_id = trade_sell_start
        while True:
            sell, _ = get('trade', f'{pair}_sell', None, str(trade_sell_id))
            if sell is None:
                break

            price = sell[3]
            dx_base = min(-sell[1], quote_balance * K // price, base_value)
            dx_quote = dx_base * price // K
            if dx_base == 0 or dx_quote == 0:
                break
            sell[1] += dx_base
            sell[2] -= dx_quote
            take_amount += dx_base

            if quote_balance - dx_quote < 0:
                break
            quote_balance -= dx_quote
            quote_sum += dx_quote

            if sell[1] == 0 or sell[1] // price == 0:
                trade_sell_start = _remove_order(addr, pair, sell, trade_sell_start, 'sell')

                if sell[1] < 0:
                    balance, _ = get(base_tick, 'balance', 0, sell[0])
                    balance -= sell[1]
                    assert balance >= 0
                    put(sell[0], base_tick, 'balance', balance, sell[0])

                put(sell[0], 'trade', f'{pair}_sell', None, str(trade_sell_id))
            else:
                put(sell[0], 'trade', f'{pair}_sell', sell, str(trade_sell_id))

            balance, _ = get(quote_tick, 'balance', 0, sell[0])
            balance += dx_quote
            assert balance >= 0
            put(addr, quote_tick, 'balance', balance, sell[0])

            base_value -= dx_base
            assert base_value >= 0
            balance, _ = get(base_tick, 'balance', 0, addr)
            balance += dx_base
            assert balance >= 0
            put(addr, base_tick, 'balance', balance, addr)

            if sell[4] is None:
                break
            trade_sell_id = sell[4]

        balance, _ = get(quote_tick, 'balance', 0, addr)
        balance -= quote_sum
        assert balance >= 0
        put(addr, quote_tick, 'balance', balance, addr)

    elif base_value is None and int(quote_value) < 0:
        buy_or_sell = 'buy'
        quote_value = int(args['a'][3])
        quote_balance, _ = get(quote_tick, 'balance', 0, addr)
        quote_sum = 0

        trade_sell_id = trade_sell_start
        while True:
            sell, _ = get('trade', f'{pair}_sell', None, str(trade_sell_id))
            if sell is None:
                break

            price = sell[3]
            dx_base = min(-sell[1], -quote_value * K // price)
            dx_quote = dx_base * price // K
            if dx_base == 0 or  dx_quote == 0:
                break
            sell[1] += dx_base
            sell[2] -= dx_quote
            take_amount += dx_base

            if quote_balance - dx_quote < 0:
                break
            quote_balance -= dx_quote
            quote_sum += dx_quote

            if sell[1] == 0 or sell[1] // price == 0:
                trade_sell_start = _remove_order(addr, pair, sell, trade_sell_start, 'sell')

                if sell[1] < 0:
                    balance, _ = get(base_tick, 'balance', 0, sell[0])
                    balance -= sell[1]
                    assert balance >= 0
                    put(sell[0], base_tick, 'balance', balance, sell[0])

                put(sell[0], 'trade', f'{pair}_sell', None, str(trade_sell_id))
            else:
                put(sell[0], 'trade', f'{pair}_sell', sell, str(trade_sell_id))

            balance, _ = get(quote_tick, 'balance', 0, sell[0])
            balance += dx_quote
            assert balance >= 0
            put(addr, quote_tick, 'balance', balance, sell[0])

            quote_value += dx_quote
            assert quote_value <= 0
            balance, _ = get(base_tick, 'balance', 0, addr)
            balance += dx_base
            assert balance >= 0
            put(addr, base_tick, 'balance', balance, addr)

            if sell[4] is None:
                break
            trade_sell_id = sell[4]

        balance, _ = get(quote_tick, 'balance', 0, addr)
        balance -= quote_sum
        assert balance >= 0
        put(addr, quote_tick, 'balance', balance, addr)

    elif base_value is None and int(quote_value) > 0:
        buy_or_sell = 'sell'
        quote_value = int(args['a'][3])
        base_balance, _ = get(base_tick, 'balance', 0, addr)
        base_sum = 0

        trade_buy_id = trade_buy_start
        while True:
            buy, _ = get('trade', f'{pair}_buy', None, str(trade_buy_id))
            if buy is None:
                break

            price = buy[3]
            dx_base = min(buy[1], base_balance, quote_value * K // price)
            dx_quote = dx_base * price // K
            if dx_base == 0 or dx_quote == 0:
                break
            buy[1] -= dx_base
            buy[2] += dx_quote
            take_amount += dx_quote

            if base_balance - dx_base < 0:
                break
            base_balance -= dx_base
            base_sum += dx_base

            if buy[1] == 0 or buy[1] // price == 0:
                trade_buy_start = _remove_order(addr, pair, buy, trade_buy_start, 'buy')

                if buy[2] < 0:
                    balance, _ = get(quote_tick, 'balance', 0, buy[0])
                    balance -= buy[2]
                    assert balance >= 0
                    put(buy[0], quote_tick, 'balance', balance, buy[0])
    
                put(buy[0], 'trade', f'{pair}_buy', None, str(trade_buy_id))
            else:
                put(buy[0], 'trade', f'{pair}_buy', buy, str(trade_buy_id))

            balance, _ = get(base_tick, 'balance', 0, buy[0])
            balance += dx_base
            assert balance >= 0
            put(addr, base_tick, 'balance', balance, buy[0])

            quote_value -= dx_quote
            assert quote_value >= 0
            balance, _ = get(quote_tick, 'balance', 0, addr)
            balance += dx_quote
            assert balance >= 0
            put(addr, quote_tick, 'balance', balance, addr)

            if buy[4] is None:
                break
            trade_buy_id = buy[4]

        balance, _ = get(base_tick, 'balance', 0, addr)
        balance -= base_sum
        assert balance >= 0
        put(addr, base_tick, 'balance', balance, addr)

    if take_amount > 0:
        cost = 0
        price = 0
        event('TradeOrderTake', [pair, buy_or_sell, addr, take_amount, price, cost])


def trade_limit_order_cancel(info, args):
    assert args['f'] == 'trade_limit_order_cancel'
    sender = info['sender']
    addr = handle_lookup(sender)

    base_tick = args['a'][1]
    assert set(base_tick) <= set(string.ascii_uppercase + '_')
    quote_tick = args['a'][2]
    assert set(quote_tick) <= set(string.ascii_uppercase + '_')
    buy_or_sell = args['a'][3]
    assert buy_or_sell in ['buy', 'sell']
    trade_order_id = int(args['a'][4])

    pair = '%s_%s' % (base_tick, quote_tick)
    order_key = f'{pair}_{buy_or_sell}'
    order, _ = get('trade', order_key, None, str(trade_order_id))

    assert order is not None, "Order does not exist"
    assert order[0] == addr, "Sender is not the owner of the order"

    prev_order_id = order[4]
    next_order_id = order[5]

    if prev_order_id is not None:
        prev_order, _ = get('trade', order_key, None, str(prev_order_id))
        if prev_order:
            prev_order[5] = next_order_id
            put(prev_order[0], 'trade', order_key, prev_order, str(prev_order_id))

    if next_order_id is not None:
        next_order, _ = get('trade', order_key, None, str(next_order_id))
        if next_order:
            next_order[4] = prev_order_id
            put(next_order[0], 'trade', order_key, next_order, str(next_order_id))

    start_key = f'{pair}_{buy_or_sell}_start'
    current_start, _ = get('trade', start_key, 1)
    if current_start == trade_order_id:
        if prev_order_id is not None:
            put(addr, 'trade', start_key, prev_order_id)
        else:
            new_start_key = f'{pair}_{buy_or_sell}_new'
            new_start_val, _ = get('trade', new_start_key, 1)
            put(addr, 'trade', start_key, new_start_val)

    if buy_or_sell == 'sell':
        if order[1] < 0:
            balance, _ = get(base_tick, 'balance', 0, addr)
            balance -= order[1]
            put(addr, base_tick, 'balance', balance, addr)
    elif buy_or_sell == 'buy':
        if order[2] < 0:
            balance, _ = get(quote_tick, 'balance', 0, addr)
            balance -= order[2]
            put(addr, quote_tick, 'balance', balance, addr)

    put(addr, 'trade', order_key, None, str(trade_order_id))
    event('TradeOrderCancel', [trade_order_id, buy_or_sell, pair])


def trade_pair_create(info, args):
    assert args['f'] == 'trade_pair_create'
    sender = info['sender']
    addr = handle_lookup(sender)

    base_tick = args['a'][0]
    quote_tick = args['a'][1]

    quote_tokens, _ = get('trade', 'quote_tokens', [])
    assert quote_tick in quote_tokens, f"{quote_tick} is not a designated quote token"

    owner, _ = get('asset', 'owner', None, base_tick)
    assert owner == addr, f"Sender must be the owner of the base token ({base_tick})"
    pair = f'{base_tick}_{quote_tick}'
    enable, _ = get('trade', f'{pair}_enable', None)
    assert enable is None, "Pair already exists"

    put(addr, 'trade', f'{pair}_enable', True)
    put(addr, 'trade', f'{pair}_buy_start', 1)
    put(addr, 'trade', f'{pair}_buy_new', 1)
    put(addr, 'trade', f'{pair}_sell_start', 1)
    put(addr, 'trade', f'{pair}_sell_new', 1)


def trade_pair_enable(info, args):
    assert args['f'] == 'trade_pair_enable'
    sender = info['sender']
    addr = handle_lookup(sender)

    base_tick = args['a'][0]
    quote_tick = args['a'][1]
    pair = f'{base_tick}_{quote_tick}'

    owner, _ = get('asset', 'owner', None, base_tick)
    assert owner == addr, f"Sender must be the owner of the base token ({base_tick})"

    put(addr, 'trade', f'{pair}_enable', True)


def trade_pair_disable(info, args):
    assert args['f'] == 'trade_pair_disable'
    sender = info['sender']
    addr = handle_lookup(sender)

    base_tick = args['a'][0]
    quote_tick = args['a'][1]
    pair = f'{base_tick}_{quote_tick}'

    owner, _ = get('asset', 'owner', None, base_tick)
    assert owner == addr, f"Sender must be the owner of the base token ({base_tick})"

    put(addr, 'trade', f'{pair}_enable', False)


def trade_set_quote_token(info, args):
    assert args['f'] == 'trade_set_quote_token'
    sender = info['sender']
    addr = handle_lookup(sender)

    treasure_manager, _ = get('trade', 'treasure_manager', None)
    assert treasure_manager is not None, "Treasure manager not set"
    assert addr == treasure_manager, "Only the treasure manager can add quote tokens"

    new_tokens = args['a'][0]
    assert isinstance(new_tokens, list), "Quote tokens must be a list"

    quote_tokens, _ = get('trade', 'quote_tokens', [])

    for token in new_tokens:
        assert isinstance(token, str), "Token ticker must be a string"
        assert set(token) <= set(string.ascii_uppercase+'_'), "Invalid characters in token ticker"
        if token not in quote_tokens:
            quote_tokens.append(token)

    put(addr, 'trade', 'quote_tokens', quote_tokens)


def trade_vote_treasure_manager(info, args):
    assert args['f'] == 'trade_vote_treasure_manager'
    sender = info['sender']
    addr = handle_lookup(sender)

    committee_members, _ = get('committee', 'members', [])
    committee_members = set(committee_members)
    assert addr in committee_members, "Only committee members can vote"

    user = args['a'][0]
    assert isinstance(user, str), "User address must be a string"

    proposal_key = f'trade_treasure_manager:{user}'
    votes, _ = get('committee', 'proposal', [], proposal_key)
    votes = set(votes)
    votes.add(addr)

    if len(votes) >= len(committee_members) * 2 // 3:
        put(addr, 'trade', 'treasure_manager', user)
        put(addr, 'committee', 'proposal', [], proposal_key)
    else:
        put(addr, 'committee', 'proposal', list(votes), proposal_key)
