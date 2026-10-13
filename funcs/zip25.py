
def _valid_slug(slug):
    assert isinstance(slug, str) and slug, "Slug must be a non-empty string"
    assert set(slug) <= set(string.ascii_lowercase+string.digits+'_'), "Invalid characters in slug"

def _insert_order(addr, pair, order_type, order_start, order_new, quote_value, base_value, mode, quote_scale):
    assert order_type in ['buy', 'sell']
    premium_price = - quote_value * quote_scale // base_value
    order_id = order_start
    while True:
        order, _ = get('options', f'{pair}_{order_type}', None, str(order_id))

        if order is None:
            put(addr, 'options', f'{pair}_{order_type}',
                [addr, base_value, quote_value, premium_price, None, None, mode], str(order_new))
            order_new += 1
            put(addr, 'options', f'{pair}_{order_type}_new', order_new)
            break

        if order_type == 'buy':
            cond = premium_price > order[3]
        else:
            cond = premium_price < order[3]

        if cond:
            next_order_id = order[5]
            put(addr, 'options', f'{pair}_{order_type}',
                [addr, base_value, quote_value, premium_price, order_id, next_order_id, mode], str(order_new))
            if next_order_id is None:
                order_start = order_new
                put(addr, 'options', f'{pair}_{order_type}_start', order_new)
            order[5] = order_new
            order_new += 1
            put(addr, 'options', f'{pair}_{order_type}_new', order_new)

            put(addr, 'options', f'{pair}_{order_type}', order, str(order_id))
            if next_order_id is not None:
                next_order, _ = get('options', f'{pair}_{order_type}', None, str(next_order_id))
                if next_order is not None:
                    next_order[4] = order[5]
                    put(addr, 'options', f'{pair}_{order_type}', next_order, str(next_order_id))
            break

        if order[4] is None:
            put(addr, 'options', f'{pair}_{order_type}',
                [addr, base_value, quote_value, premium_price, None, order_id, mode], str(order_new))
            put(addr, 'options', f'{pair}_{order_type}',
                [order[0], order[1], order[2], order[3], order_new, order[5], order[6]], str(order_id))
            order_new += 1
            put(addr, 'options', f'{pair}_{order_type}_new', order_new)
            break

        order_id = order[4]
    return order_start, order_new

def _remove_order(addr, pair, order, order_start, buy_or_sell):
    assert buy_or_sell in ['buy', 'sell']
    if order[4]:
        prev_order, _ = get('options', f'{pair}_{buy_or_sell}', None, str(order[4]))
        prev_order[5] = order[5]
        put(prev_order[0], 'options', f'{pair}_{buy_or_sell}', prev_order, str(order[4]))

    if order[5]:
        next_order, _ = get('options', f'{pair}_{buy_or_sell}', None, str(order[5]))
        next_order[4] = order[4]
        put(next_order[0], 'options', f'{pair}_{buy_or_sell}', next_order, str(order[5]))

    if order[4] is not None and order[5] is None:
        order_start = order[4]
        put(addr, 'options', f'{pair}_{buy_or_sell}_start', order_start)

    elif order[4] is None and order[5] is None:
        order_new, _ = get('options', f'{pair}_{buy_or_sell}_new', 1)
        order_start = order_new
        put(addr, 'options', f'{pair}_{buy_or_sell}_start', order_start)

    return order_start

def _update_claim(addr, pair, delta):
    prev, manager = get('options', f'{pair}_claim_new', None)
    claim_tuple, _ = get('options', f'{pair}_claim', None, addr)
    if claim_tuple is None:
        claim = 0
    else:
        claim = claim_tuple[0]
        prev = claim_tuple[1]
    claim += delta
    assert claim >= 0, "Claim balance underflow"
    if claim_tuple is None:
        put(manager, 'options', f'{pair}_claim_new', addr)
    put(addr, 'options', f'{pair}_claim', [claim, prev], addr)

def _update_locked(addr, pair, delta):
    prev, manager = get('options', f'{pair}_locked_new', None)
    locked_tuple, _ = get('options', f'{pair}_locked', None, addr)
    if locked_tuple is None:
        locked = 0
    else:
        locked = locked_tuple[0]
        prev = locked_tuple[1]
    locked += delta
    assert locked >= 0, "Locked collateral underflow"
    if locked_tuple is None:
        put(manager, 'options', f'{pair}_locked_new', addr)
    put(addr, 'options', f'{pair}_locked', [locked, prev], addr)

def _update_escrow(addr, pair, delta):
    escrow, _ = get('options', f'{pair}_escrow', 0, addr)
    escrow = escrow or 0
    escrow += delta
    assert escrow >= 0, "Escrow balance underflow"
    put(addr, 'options', f'{pair}_escrow', escrow or None, addr)

def _update_quote_balance(addr, quote_tick, delta):
    balance, _ = get(quote_tick, 'balance', 0, addr)
    balance += delta
    assert balance >= 0
    put(addr, quote_tick, 'balance', balance, addr)

def _update_base_balance(addr, base_tick, delta):
    balance, _ = get(base_tick, 'balance', 0, addr)
    balance += delta
    assert balance >= 0, "Base balance underflow"
    put(addr, base_tick, 'balance', balance, addr)

def _pot_addr(slug):
    return f'pot_options:{slug}'

def _update_pot_balance(slug, base_tick, delta):
    """The pot's base balance is owned by the options manager, not by the pot
    address itself: the manager is the custodian of the escrowed collateral."""
    manager, _ = get('options', 'manager', None)
    assert manager is not None, "Manager not set"
    pot = _pot_addr(slug)
    balance, _ = get(base_tick, 'balance', 0, pot)
    balance = balance or 0
    balance += delta
    assert balance >= 0, "Pot base balance underflow"
    put(manager, base_tick, 'balance', balance or None, pot)

def _decimal(tick):
    """On-chain token decimals, used to scale base raw amounts back to units."""
    dec, _ = get(tick, 'decimal', None)
    assert dec is not None, f'{tick} has no registered decimals'
    return int(dec)


def _market(slug):
    _valid_slug(slug)
    base_tick, _ = get('options', f'{slug}_base_token', None)
    quote_tick, _ = get('options', f'{slug}_quote_token', None)
    assert base_tick and quote_tick, "Market not found"
    strike, _ = get('options', f'{slug}_strike', None)
    assert strike is not None, "Strike not registered"
    return base_tick, quote_tick, strike

def _collateralize(addr, pair, slug, call_or_put, base_tick, quote_tick, strike, base_amount):
    """A call writer locks base (covered); a put writer locks quote equal to
    the strike per base unit (cash-secured). The escrow ledger itself always
    counts claims (base units); only the currency moved differs."""
    assert base_amount > 0, "Collateral amount must be positive"
    if call_or_put == 'call':
        _update_base_balance(addr, base_tick, -base_amount)
        _update_pot_balance(slug, base_tick, base_amount)
    else:
        # strike is stored as quote raw units per base unit, so n base-raw
        # claims lock n * strike / base_scale quote-raw. Ceil so the pot can
        # never underflow against floor-valued payouts.
        base_scale = 10 ** _decimal(base_tick)
        quote_amount = (base_amount * strike + base_scale - 1) // base_scale
        _update_quote_balance(addr, quote_tick, -quote_amount)
        _update_pot_balance(slug, quote_tick, quote_amount)
    _update_escrow(addr, pair, base_amount)

def _release_escrow(order, pair, slug, call_or_put, base_tick, quote_tick, strike):
    """Refund the remaining collateral of a resting write-mode sell order."""
    if order[1] >= 0:
        return
    if call_or_put == 'call':
        _update_base_balance(order[0], base_tick, -order[1])
        _update_pot_balance(slug, base_tick, order[1])
    else:
        base_scale = 10 ** _decimal(base_tick)
        quote_amount = (-order[1]) * strike // base_scale
        _update_quote_balance(order[0], quote_tick, quote_amount)
        _update_pot_balance(slug, quote_tick, -quote_amount)
    _update_escrow(order[0], pair, order[1])

def _clear_book(addr, pair, call_or_put, slug, base_tick, quote_tick, strike):
    for order_type in ['sell', 'buy']:
        order_id, _ = get('options', f'{pair}_{order_type}_start', 1)
        while order_id is not None:
            order, _ = get('options', f'{pair}_{order_type}', None, str(order_id))
            if order is None:
                break
            next_id = order[4]
            if order_type == 'sell':
                if order[6] == 'write':
                    _release_escrow(order, pair, slug, call_or_put, base_tick, quote_tick, strike)
                elif order[1] < 0:
                    _update_claim(order[0], pair, -order[1])
            else:
                if order[2] < 0:
                    _update_quote_balance(order[0], quote_tick, -order[2])
            put(order[0], 'options', f'{pair}_{order_type}', None, str(order_id))
            order_id = next_id
        put(addr, 'options', f'{pair}_{order_type}_start', None)
        put(addr, 'options', f'{pair}_{order_type}_new', None)


def options_limit_buy(info, args):
    assert args['f'] == 'options_limit_buy'
    sender = info['sender']
    addr = handle_lookup(sender)

    slug = args['a'][0]
    base_tick, quote_tick, _strike = _market(slug)
    quote_scale = 10 ** _decimal(quote_tick)

    call_or_put = args['a'][1]
    assert call_or_put in set(['call', 'put'])
    pair = f'{slug}_{call_or_put}'

    base_value = int(args['a'][2])
    quote_value = int(args['a'][3])
    assert base_value > 0 and quote_value < 0, "options_limit_buy requires a buy (positive base, negative quote)"

    options_buy_start, _ = get('options', f'{pair}_buy_start', 1)
    options_buy_new, _ = get('options', f'{pair}_buy_new', 1)
    options_sell_start, _ = get('options', f'{pair}_sell_start', 1)
    options_sell_new, _ = get('options', f'{pair}_sell_new', 1)

    buy_or_sell = 'buy'
    _update_quote_balance(addr, quote_tick, quote_value)
    make_base = base_value

    order_id = options_buy_new
    options_buy_start, options_buy_new = _insert_order(addr, pair, 'buy', options_buy_start, options_buy_new, quote_value, base_value, None, quote_scale)

    options_sell_id = options_sell_start
    highest_buy_premium_price = None

    take_base = 0
    take_quote = 0
    while True:
        sell, _ = get('options', f'{pair}_sell', None, str(options_sell_id))
        if not sell:
            break
        sell_premium_price = sell[3]
        if highest_buy_premium_price and sell_premium_price > highest_buy_premium_price:
            break

        options_buy_id = options_buy_start
        while True:
            buy, _ = get('options', f'{pair}_buy', None, str(options_buy_id))
            if not buy:
                break
            buy_premium_price = buy[3]
            if highest_buy_premium_price is None:
                highest_buy_premium_price = buy_premium_price
            if sell_premium_price > buy_premium_price:
                options_buy_id = buy[4]
                continue

            matched_premium_price = sell_premium_price
            dx_base = min(-sell[1], buy[1])
            dx_quote = dx_base * matched_premium_price // quote_scale
            sell[1] += dx_base
            sell[2] -= dx_quote
            buy[1] -= dx_base
            buy[2] += dx_quote
            take_base += dx_base
            take_quote += dx_quote

            _update_claim(buy[0], pair, dx_base)
            if sell[6] == 'write':
                _update_escrow(sell[0], pair, -dx_base)
                _update_locked(sell[0], pair, dx_base)
            _update_quote_balance(sell[0], quote_tick, dx_quote)
            if buy[1] == 0:
                options_buy_start = _remove_order(addr, pair, buy, options_buy_start, 'buy')
                if buy[2] < 0:
                    _update_quote_balance(buy[0], quote_tick, -buy[2])

                put(buy[0], 'options', f'{pair}_buy', None, str(options_buy_id))
            else:
                put(buy[0], 'options', f'{pair}_buy', buy, str(options_buy_id))

            if sell[1] == 0:
                break
            if buy[4] is None:
                break
            options_buy_id = buy[4]

        if sell[1] == 0:
            options_sell_start = _remove_order(addr, pair, sell, options_sell_start, 'sell')
            put(sell[0], 'options', f'{pair}_sell', None, str(options_sell_id))
        else:
            put(sell[0], 'options', f'{pair}_sell', sell, str(options_sell_id))

        if sell[4] is None:
            break
        options_sell_id = sell[4]

    make_base -= take_base
    assert make_base >= 0
    make_premium_price = - quote_value * quote_scale // base_value
    event('OptionsLimitMake', [pair, buy_or_sell, addr, make_base, make_premium_price, order_id])
    if take_base > 0:
        take_premium_price = take_quote * quote_scale // take_base
        event('OptionsLimitTake', [pair, buy_or_sell, addr, take_base, take_premium_price, order_id])


def options_limit_sell(info, args):
    assert args['f'] == 'options_limit_sell'
    sender = info['sender']
    addr = handle_lookup(sender)

    slug = args['a'][0]
    base_tick, quote_tick, strike = _market(slug)
    quote_scale = 10 ** _decimal(quote_tick)

    call_or_put = args['a'][1]
    assert call_or_put in set(['call', 'put'])
    pair = f'{slug}_{call_or_put}'

    base_value = int(args['a'][2])
    quote_value = int(args['a'][3])
    assert base_value < 0 and quote_value > 0, "options_limit_sell requires a sell (negative base, positive quote)"

    mode = args['a'][4] if len(args['a']) > 4 else 'write'
    assert mode in ('write', 'claim'), "mode must be 'write' (collateralize new base) or 'claim' (sell held claims)"

    options_buy_start, _ = get('options', f'{pair}_buy_start', 1)
    options_buy_new, _ = get('options', f'{pair}_buy_new', 1)
    options_sell_start, _ = get('options', f'{pair}_sell_start', 1)
    options_sell_new, _ = get('options', f'{pair}_sell_new', 1)

    buy_or_sell = 'sell'
    make_base = - base_value
    if mode == 'write':
        _collateralize(addr, pair, slug, call_or_put, base_tick, quote_tick, strike, make_base)
    else:
        _update_claim(addr, pair, -make_base)

    order_id = options_sell_new
    options_sell_start, options_sell_new = _insert_order(addr, pair, 'sell', options_sell_start, options_sell_new, quote_value, base_value, mode, quote_scale)

    options_sell_id = options_sell_start
    highest_buy_premium_price = None

    take_base = 0
    take_quote = 0
    while True:
        sell, _ = get('options', f'{pair}_sell', None, str(options_sell_id))
        if not sell:
            break
        sell_premium_price = sell[3]
        if highest_buy_premium_price and sell_premium_price > highest_buy_premium_price:
            break

        options_buy_id = options_buy_start
        while True:
            buy, _ = get('options', f'{pair}_buy', None, str(options_buy_id))
            if not buy:
                break
            buy_premium_price = buy[3]
            if highest_buy_premium_price is None:
                highest_buy_premium_price = buy_premium_price
            if sell_premium_price > buy_premium_price:
                options_buy_id = buy[4]
                continue

            matched_premium_price = sell_premium_price
            dx_base = min(-sell[1], buy[1])
            dx_quote = dx_base * matched_premium_price // quote_scale
            sell[1] += dx_base
            sell[2] -= dx_quote
            buy[1] -= dx_base
            buy[2] += dx_quote
            take_base += dx_base
            take_quote += dx_quote

            _update_claim(buy[0], pair, dx_base)
            if sell[6] == 'write':
                _update_escrow(sell[0], pair, -dx_base)
                _update_locked(sell[0], pair, dx_base)
            _update_quote_balance(sell[0], quote_tick, dx_quote)
            if buy[1] == 0:
                options_buy_start = _remove_order(addr, pair, buy, options_buy_start, 'buy')
                if buy[2] < 0:
                    _update_quote_balance(buy[0], quote_tick, -buy[2])

                put(buy[0], 'options', f'{pair}_buy', None, str(options_buy_id))
            else:
                put(buy[0], 'options', f'{pair}_buy', buy, str(options_buy_id))

            if sell[1] == 0:
                break
            if buy[4] is None:
                break
            options_buy_id = buy[4]

        if sell[1] == 0:
            options_sell_start = _remove_order(addr, pair, sell, options_sell_start, 'sell')
            put(sell[0], 'options', f'{pair}_sell', None, str(options_sell_id))
        else:
            put(sell[0], 'options', f'{pair}_sell', sell, str(options_sell_id))

        if sell[4] is None:
            break
        options_sell_id = sell[4]

    make_base -= take_base
    assert make_base >= 0
    make_premium_price = - quote_value * quote_scale // base_value
    event('OptionsLimitMake', [pair, buy_or_sell, addr, make_base, make_premium_price, order_id])
    if take_base > 0:
        take_premium_price = take_quote * quote_scale // take_base
        event('OptionsLimitTake', [pair, buy_or_sell, addr, take_base, take_premium_price, order_id])


def options_market_order(info, args):
    assert args['f'] == 'options_market_order'
    sender = info['sender']
    addr = handle_lookup(sender)

    slug = args['a'][0]
    base_tick, quote_tick, strike = _market(slug)
    quote_scale = 10 ** _decimal(quote_tick)

    call_or_put = args['a'][1]
    assert call_or_put in set(['call', 'put'])
    pair = f'{slug}_{call_or_put}'

    base_value = args['a'][2]
    quote_value = args['a'][3]
    options_sell_start, _ = get('options', f'{pair}_sell_start', 1)
    options_buy_start, _ = get('options', f'{pair}_buy_start', 1)

    take_base = 0
    take_quote = 0
    if quote_value is None and int(base_value) < 0:
        buy_or_sell = 'sell'
        base_value = int(args['a'][2])
        claim_tuple, _ = get('options', f'{pair}_claim', [0, None], addr)
        base_balance = claim_tuple[0] if claim_tuple else 0

        options_buy_id = options_buy_start
        while True:
            buy, _ = get('options', f'{pair}_buy', None, str(options_buy_id))
            if buy is None:
                break

            premium_price = buy[3]
            dx_base = min(buy[1], -buy[2] * quote_scale // premium_price, -base_value)
            dx_quote = dx_base * premium_price // quote_scale
            if dx_base == 0 or dx_quote == 0:
                break
            if base_balance - dx_base < 0:
                break
            buy[1] -= dx_base
            buy[2] += dx_quote
            take_base += dx_base
            take_quote += dx_quote
            base_balance -= dx_base

            if buy[1] == 0 or buy[1] * quote_scale // premium_price == 0:
                options_buy_start = _remove_order(addr, pair, buy, options_buy_start, 'buy')
                if buy[2] < 0:
                    _update_quote_balance(buy[0], quote_tick, -buy[2])

                put(buy[0], 'options', f'{pair}_buy', None, str(options_buy_id))
            else:
                put(buy[0], 'options', f'{pair}_buy', buy, str(options_buy_id))

            _update_claim(buy[0], pair, dx_base)
            base_value += dx_base
            assert base_value <= 0

            _update_quote_balance(addr, quote_tick, dx_quote)
            if buy[4] is None:
                break
            options_buy_id = buy[4]

        _update_claim(addr, pair, -take_base)

    elif quote_value is None and int(base_value) > 0:
        buy_or_sell = 'buy'
        base_value = int(args['a'][2])
        quote_balance, _ = get(quote_tick, 'balance', 0, addr)

        options_sell_id = options_sell_start
        while True:
            sell, _ = get('options', f'{pair}_sell', None, str(options_sell_id))
            if sell is None:
                break

            premium_price = sell[3]
            dx_base = min(-sell[1], quote_balance * quote_scale // premium_price, base_value)
            dx_quote = dx_base * premium_price // quote_scale
            if dx_base == 0 or dx_quote == 0:
                break
            if quote_balance - dx_quote < 0:
                break

            sell[1] += dx_base
            sell[2] -= dx_quote
            take_base += dx_base
            take_quote += dx_quote
            quote_balance -= dx_quote

            if sell[1] == 0 or sell[1] * quote_scale // premium_price == 0:
                options_sell_start = _remove_order(addr, pair, sell, options_sell_start, 'sell')
                if sell[6] == 'write':
                    _release_escrow(sell, pair, slug, call_or_put, base_tick, quote_tick, strike)
                elif sell[1] < 0:
                    _update_claim(sell[0], pair, -sell[1])

                put(sell[0], 'options', f'{pair}_sell', None, str(options_sell_id))
            else:
                put(sell[0], 'options', f'{pair}_sell', sell, str(options_sell_id))

            if sell[6] == 'write':
                _update_escrow(sell[0], pair, -dx_base)
                _update_locked(sell[0], pair, dx_base)
            _update_quote_balance(sell[0], quote_tick, dx_quote)
            base_value -= dx_base
            assert base_value >= 0

            _update_claim(addr, pair, dx_base)
            if sell[4] is None:
                break
            options_sell_id = sell[4]

        _update_quote_balance(addr, quote_tick, -take_quote)

    elif base_value is None and int(quote_value) < 0:
        buy_or_sell = 'buy'
        quote_value = int(args['a'][3])
        quote_balance, _ = get(quote_tick, 'balance', 0, addr)

        options_sell_id = options_sell_start
        while True:
            sell, _ = get('options', f'{pair}_sell', None, str(options_sell_id))
            if sell is None:
                break

            premium_price = sell[3]
            dx_base = min(-sell[1], -quote_value * quote_scale // premium_price)
            dx_quote = dx_base * premium_price // quote_scale
            if dx_base == 0 or  dx_quote == 0:
                break
            if quote_balance - dx_quote < 0:
                break

            sell[1] += dx_base
            sell[2] -= dx_quote
            take_base += dx_base
            take_quote += dx_quote
            quote_balance -= dx_quote

            if sell[1] == 0 or sell[1] * quote_scale // premium_price == 0:
                options_sell_start = _remove_order(addr, pair, sell, options_sell_start, 'sell')
                if sell[6] == 'write':
                    _release_escrow(sell, pair, slug, call_or_put, base_tick, quote_tick, strike)
                elif sell[1] < 0:
                    _update_claim(sell[0], pair, -sell[1])

                put(sell[0], 'options', f'{pair}_sell', None, str(options_sell_id))
            else:
                put(sell[0], 'options', f'{pair}_sell', sell, str(options_sell_id))

            if sell[6] == 'write':
                _update_escrow(sell[0], pair, -dx_base)
                _update_locked(sell[0], pair, dx_base)
            _update_quote_balance(sell[0], quote_tick, dx_quote)
            quote_value += dx_quote
            assert quote_value <= 0

            _update_claim(addr, pair, dx_base)
            if sell[4] is None:
                break
            options_sell_id = sell[4]

        _update_quote_balance(addr, quote_tick, -take_quote)

    elif base_value is None and int(quote_value) > 0:
        buy_or_sell = 'sell'
        quote_value = int(args['a'][3])
        claim_tuple, _ = get('options', f'{pair}_claim', [0, None], addr)
        base_balance = claim_tuple[0] if claim_tuple else 0

        options_buy_id = options_buy_start
        while True:
            buy, _ = get('options', f'{pair}_buy', None, str(options_buy_id))
            if buy is None:
                break

            premium_price = buy[3]
            dx_base = min(buy[1], base_balance, quote_value * quote_scale // premium_price)
            dx_quote = dx_base * premium_price // quote_scale
            if dx_base == 0 or dx_quote == 0:
                break
            if base_balance - dx_base < 0:
                break

            buy[1] -= dx_base
            buy[2] += dx_quote
            take_base += dx_base
            take_quote += dx_quote
            base_balance -= dx_base

            if buy[1] == 0 or buy[1] * quote_scale // premium_price == 0:
                options_buy_start = _remove_order(addr, pair, buy, options_buy_start, 'buy')
                if buy[2] < 0:
                    _update_quote_balance(buy[0], quote_tick, -buy[2])

                put(buy[0], 'options', f'{pair}_buy', None, str(options_buy_id))
            else:
                put(buy[0], 'options', f'{pair}_buy', buy, str(options_buy_id))

            _update_claim(buy[0], pair, dx_base)
            quote_value -= dx_quote
            assert quote_value >= 0
            _update_quote_balance(addr, quote_tick, dx_quote)

            if buy[4] is None:
                break
            options_buy_id = buy[4]

        _update_claim(addr, pair, -take_base)

    if take_base > 0:
        premium_price = take_quote * quote_scale // take_base
        event('OptionsMarketTake', [pair, buy_or_sell, addr, take_base, premium_price])


def options_limit_order_cancel(info, args):
    assert args['f'] == 'options_limit_order_cancel'
    sender = info['sender']
    addr = handle_lookup(sender)

    slug = args['a'][0]
    call_or_put = args['a'][1]
    buy_or_sell = args['a'][2]
    options_order_id = int(args['a'][3])
    assert call_or_put in set(['call', 'put'])
    assert buy_or_sell in ['buy', 'sell']
    assert options_order_id > 0

    base_tick, quote_tick, strike = _market(slug)

    pair = f'{slug}_{call_or_put}'
    order_key = f'{pair}_{buy_or_sell}'
    order, _ = get('options', order_key, None, str(options_order_id))

    if order is None:
        return

    assert order[0] == addr, "Sender is not the owner of the order"
    prev_order_id = order[4]
    next_order_id = order[5]

    if prev_order_id is not None:
        prev_order, _ = get('options', order_key, None, str(prev_order_id))
        if prev_order:
            prev_order[5] = next_order_id
            put(prev_order[0], 'options', order_key, prev_order, str(prev_order_id))

    if next_order_id is not None:
        next_order, _ = get('options', order_key, None, str(next_order_id))
        if next_order:
            next_order[4] = prev_order_id
            put(next_order[0], 'options', order_key, next_order, str(next_order_id))

    start_key = f'{pair}_{buy_or_sell}_start'
    current_start, _ = get('options', start_key, 1)
    if current_start == options_order_id:
        if prev_order_id is not None:
            put(addr, 'options', start_key, prev_order_id)
        else:
            new_start_key = f'{pair}_{buy_or_sell}_new'
            new_start_val, _ = get('options', new_start_key, 1)
            put(addr, 'options', start_key, new_start_val)

    if buy_or_sell == 'sell':
        if order[6] == 'write':
            _release_escrow(order, pair, slug, call_or_put, base_tick, quote_tick, strike)
        elif order[1] < 0:
            _update_claim(addr, pair, -order[1])
    elif buy_or_sell == 'buy':
        if order[2] < 0:
            _update_quote_balance(addr, quote_tick, -order[2])

    put(addr, 'options', order_key, None, str(options_order_id))
    event('OptionsOrderCancel', [options_order_id, buy_or_sell, pair])


def options_create(info, args):
    assert args['f'] == 'options_create'
    sender = info['sender']
    addr = handle_lookup(sender)

    slug = args['a'][0]
    _valid_slug(slug)
    quote_tick = args['a'][1]
    base_tick = args['a'][2]
    strike = int(args['a'][3])
    assert strike > 0, "Strike must be positive"
    assert base_tick != quote_tick, "Base and quote token must differ"

    quote_tokens, _ = get('options', 'quote_tokens', [])
    assert quote_tick in quote_tokens, f'{quote_tick} is not a designated quote token'

    base_owner, _ = get('asset', 'owner', None, base_tick)
    assert base_owner, f'{base_tick} is not a valid asset'

    manager, _ = get('options', 'manager', None)
    assert manager == addr, f"Sender must be the owner of options system"

    created, _ = get('options', f'{slug}_strike', None)
    assert created is None, "Market already exists"

    put(addr, 'options', f'{slug}_base_token', base_tick)
    put(addr, 'options', f'{slug}_quote_token', quote_tick)
    put(addr, 'options', f'{slug}_strike', strike)

    for tick in ['call', 'put']:
        pair = f'{slug}_{tick}'
        put(addr, 'options', f'{pair}_buy_start', 1)
        put(addr, 'options', f'{pair}_buy_new', 1)
        put(addr, 'options', f'{pair}_sell_start', 1)
        put(addr, 'options', f'{pair}_sell_new', 1)
        put(addr, 'options', f'{pair}_claim_new', None)
        put(addr, 'options', f'{pair}_locked_new', None)

    event('OptionsMarketCreate', [slug, quote_tick, base_tick, strike, addr])


def options_submit(info, args):
    assert args['f'] == 'options_submit'
    sender = info['sender']
    addr = handle_lookup(sender)

    manager, _ = get('options', 'manager', None)
    assert manager is not None, "Manager not set"
    assert addr == manager, "Only the manager can submit result"

    slug = args['a'][0]
    expiry_price = int(args['a'][1])
    assert expiry_price > 0, "Expiry price must be positive"

    # _market asserts the market exists, the slug format is valid, and that it has not settled yet.
    base_tick, quote_tick, strike = _market(slug)
    # strike and expiry_price are both quote raw units per base unit; claims
    # are base raw units, so payouts divide by the base scale.
    base_scale = 10 ** _decimal(base_tick)

    pot = _pot_addr(slug)
    if expiry_price >= strike:
        win_tick, lose_tick = 'call', 'put'
    else:
        win_tick, lose_tick = 'put', 'call'

    win_pair = f'{slug}_{win_tick}'
    lose_pair = f'{slug}_{lose_tick}'

    # Closing a book unwinds every resting order: write-mode sell orders get
    # their collateral back, claim-mode sell orders get their claims back, and
    # buy orders get their reserved quote back.
    _clear_book(addr, win_pair, win_tick, slug, base_tick, quote_tick, strike)
    _clear_book(addr, lose_pair, lose_tick, slug, base_tick, quote_tick, strike)

    if win_tick == 'call':
        # In the money, settled in kind: a covered call writes at the strike,
        # so a claim only receives its intrinsic gain at the expiry price,
        # paid in base. payout = claim * (expiry - strike) / expiry is a
        # dimensionless ratio of the two quote prices times a base amount, and
        # the product is floored once per holder, never per claim.
        current_addr, _ = get('options', f'{win_pair}_claim_new', None)
        while current_addr is not None:
            claim_tuple, _ = get('options', f'{win_pair}_claim', None, current_addr)
            if claim_tuple is None:
                break
            claim, prev = claim_tuple
            assert claim >= 0, "Negative claim balance at settlement"
            payout = claim * (expiry_price - strike) // expiry_price
            if payout > 0:
                _update_base_balance(current_addr, base_tick, payout)
                _update_pot_balance(slug, base_tick, -payout)
            put(current_addr, 'options', f'{win_pair}_claim', None, current_addr)
            current_addr = prev
        put(addr, 'options', f'{win_pair}_claim_new', None)

        # The writers are refunded the rest of their collateral in base
        # (locked * strike / expiry); the last writer absorbs the rounding dust
        # so the pot drains to exactly zero.
        current_addr, _ = get('options', f'{win_pair}_locked_new', None)
        while current_addr is not None:
            locked_tuple, _ = get('options', f'{win_pair}_locked', None, current_addr)
            if locked_tuple is None:
                break
            locked, prev = locked_tuple
            assert locked >= 0, "Negative locked collateral at settlement"
            if prev is None:
                refund, _ = get(base_tick, 'balance', 0, pot)
                refund = refund or 0
            else:
                refund = locked * strike // expiry_price
            if refund > 0:
                _update_base_balance(current_addr, base_tick, refund)
                _update_pot_balance(slug, base_tick, -refund)
            put(current_addr, 'options', f'{win_pair}_locked', None, current_addr)
            current_addr = prev
        put(addr, 'options', f'{win_pair}_locked_new', None)
    else:
        # In the money, cash settled: every put claim pays its intrinsic
        # value (strike - expiry price) in quote out of the pot. The product
        # is floored once per holder, never per claim.
        current_addr, _ = get('options', f'{win_pair}_claim_new', None)
        while current_addr is not None:
            claim_tuple, _ = get('options', f'{win_pair}_claim', None, current_addr)
            if claim_tuple is None:
                break
            claim, prev = claim_tuple
            assert claim >= 0, "Negative claim balance at settlement"
            payout = claim * (strike - expiry_price) // base_scale
            if payout > 0:
                _update_quote_balance(current_addr, quote_tick, payout)
                _update_pot_balance(slug, quote_tick, -payout)
            put(current_addr, 'options', f'{win_pair}_claim', None, current_addr)
            current_addr = prev
        put(addr, 'options', f'{win_pair}_claim_new', None)

        # Each writer locked the strike per base unit and paid out the intrinsic
        # value, so they are refunded the expiry price per committed base unit.
        # The last writer in the walk absorbs the rounding dust so the pot
        # drains to exactly zero.
        current_addr, _ = get('options', f'{win_pair}_locked_new', None)
        while current_addr is not None:
            locked_tuple, _ = get('options', f'{win_pair}_locked', None, current_addr)
            if locked_tuple is None:
                break
            locked, prev = locked_tuple
            assert locked >= 0, "Negative locked collateral at settlement"
            if prev is None:
                refund, _ = get(quote_tick, 'balance', 0, pot)
                refund = refund or 0
            else:
                refund = locked * expiry_price // base_scale
            if refund > 0:
                _update_quote_balance(current_addr, quote_tick, refund)
                _update_pot_balance(slug, quote_tick, -refund)
            put(current_addr, 'options', f'{win_pair}_locked', None, current_addr)
            current_addr = prev
        put(addr, 'options', f'{win_pair}_locked_new', None)

    # Out of the money: claims lapse worthless.
    current_addr, _ = get('options', f'{lose_pair}_claim_new', None)
    while current_addr is not None:
        claim_tuple, _ = get('options', f'{lose_pair}_claim', None, current_addr)
        if claim_tuple is None:
            break
        prev = claim_tuple[1]
        put(current_addr, 'options', f'{lose_pair}_claim', None, current_addr)
        current_addr = prev
    put(addr, 'options', f'{lose_pair}_claim_new', None)

    if lose_tick == 'call':
        # Out of the money call writers get their locked base back.
        current_addr, _ = get('options', f'{lose_pair}_locked_new', None)
        while current_addr is not None:
            locked_tuple, _ = get('options', f'{lose_pair}_locked', None, current_addr)
            if locked_tuple is None:
                break
            locked, prev = locked_tuple
            assert locked >= 0, "Negative locked collateral at settlement"
            if locked > 0:
                _update_base_balance(current_addr, base_tick, locked)
                _update_pot_balance(slug, base_tick, -locked)
            put(current_addr, 'options', f'{lose_pair}_locked', None, current_addr)
            current_addr = prev
        put(addr, 'options', f'{lose_pair}_locked_new', None)
    else:
        # Out of the money put writers get their locked quote back at the
        # full strike; the last writer absorbs any rounding dust.
        current_addr, _ = get('options', f'{lose_pair}_locked_new', None)
        while current_addr is not None:
            locked_tuple, _ = get('options', f'{lose_pair}_locked', None, current_addr)
            if locked_tuple is None:
                break
            locked, prev = locked_tuple
            assert locked >= 0, "Negative locked collateral at settlement"
            if prev is None:
                refund, _ = get(quote_tick, 'balance', 0, pot)
                refund = refund or 0
            else:
                refund = locked * strike // base_scale
            if refund > 0:
                _update_quote_balance(current_addr, quote_tick, refund)
                _update_pot_balance(slug, quote_tick, -refund)
            put(current_addr, 'options', f'{lose_pair}_locked', None, current_addr)
            current_addr = prev
        put(addr, 'options', f'{lose_pair}_locked_new', None)

    pot_base, _ = get(base_tick, 'balance', 0, pot)
    pot_base = pot_base or 0
    assert pot_base == 0, "Escrow pot base not fully distributed"
    pot_quote, _ = get(quote_tick, 'balance', 0, pot)
    pot_quote = pot_quote or 0
    assert pot_quote == 0, "Escrow pot quote not fully distributed"

    # Retire the market: the strike is the market-existence signal, so clearing
    # it (and the registered tokens) lets the slug be reused by options_create.
    put(addr, 'options', f'{slug}_strike', None)
    put(addr, 'options', f'{slug}_base_token', None)
    put(addr, 'options', f'{slug}_quote_token', None)
    event('OptionsSubmit', [slug, expiry_price, strike, win_tick, addr])


def options_set_quote_tokens(info, args):
    assert args['f'] == 'options_set_quote_tokens'
    sender = info['sender']
    addr = handle_lookup(sender)

    manager, _ = get('options', 'manager', None)
    assert manager is not None, "Manager not set"
    assert addr == manager, "Only the manager can add quote tokens"

    new_tokens = args['a'][0]
    assert isinstance(new_tokens, list), "Quote tokens must be a list"

    quote_tokens, _ = get('options', 'quote_tokens', [])

    for token in new_tokens:
        assert isinstance(token, str), "Token ticker must be a string"
        assert len(token) > 0 and len(token) < 42, "Invalid token ticker length"
        assert token[0] in string.ascii_uppercase, "Token ticker must start with an uppercase letter"
        assert set(token) <= set(string.ascii_uppercase+string.digits+'_'), "Invalid characters in token ticker"
        if token not in quote_tokens:
            quote_tokens.append(token)

    put(addr, 'options', 'quote_tokens', quote_tokens)


def options_update_manager(info, args):
    assert args['f'] == 'options_update_manager'
    sender = info['sender']
    addr = handle_lookup(sender)

    manager, _ = get('options', 'manager', None)
    assert manager is not None, "Vote manager first"
    assert addr == manager, "Only the current manager can change manager"

    user = args['a'][0]
    assert isinstance(user, str), "User address must be a string"
    put(addr, 'options', 'manager', user)
    event('OptionsUpdateManager', [addr, user])


def options_vote_manager(info, args):
    assert args['f'] == 'options_vote_manager'
    sender = info['sender']
    addr = handle_lookup(sender)

    manager, _ = get('options', 'manager', None)
    assert manager is None, "Manager already set, use options_set_manager instead"

    committee_members, _ = get('committee', 'members', [])
    committee_members = set(committee_members)
    assert addr in committee_members, "Only committee members can vote"

    user = args['a'][0]
    assert isinstance(user, str), "User address must be a string"

    proposal_key = f'options_manager:{user}'
    votes, _ = get('committee', 'proposal', [], proposal_key)
    votes = set(votes)
    votes.add(addr)

    if len(votes) >= len(committee_members) * 2 // 3:
        put(addr, 'options', 'manager', user)
        put(addr, 'committee', 'proposal', [], proposal_key)
        event('OptionsUpdateManager', [list(votes), user])
    else:
        put(addr, 'committee', 'proposal', list(votes), proposal_key)

