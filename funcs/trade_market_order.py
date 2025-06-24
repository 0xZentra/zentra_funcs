def trade_market_order(info, args):
    assert args['f'] == 'trade_market_order'
    sender = info['sender']
    handle = handle_lookup(sender)
    addr = handle or sender

    base_tick = args['a'][0]
    quote_tick = args['a'][2]
    assert set(base_tick) <= set(string.ascii_uppercase+'_')
    assert set(quote_tick) <= set(string.ascii_uppercase+'_')
    pair = '%s_%s' % tuple([base_tick, quote_tick])

    base_value = args['a'][1]
    quote_value = args['a'][3]
    trade_sell_start = get('trade', f'{pair}_sell_start', 1)
    trade_buy_start = get('trade', f'{pair}_buy_start', 1)

    K = 10**18
    if quote_value is None and base_value < 0:
        balance = get(base_tick, 'balance', 0, addr)
        # print('base_tick balance', balance, addr)
        balance += base_value
        assert balance >= 0
        put(addr, base_tick, 'balance', balance, addr) # consider delay put

        trade_buy_no = trade_buy_start
        while True:
            buy = get('trade', f'{pair}_buy', None, str(trade_buy_no))
            if buy is None:
                break

            price = - buy[2] * K // buy[1]
            dx = min(buy[1], -buy[2] * K // price, -base_value)
            buy[1] -= dx
            buy[2] += dx * price // K
            if buy[1] == 0 and buy[2] == 0:
                put('', 'trade', f'{pair}_buy', None, str(trade_buy_no))
                if buy[4] is None:
                    trade_buy_new = get('trade', f'{pair}_buy_new', 1)
                    put('', 'trade', f'{pair}_buy_start', trade_buy_new)
                else:
                    put('', 'trade', f'{pair}_buy_start', buy[4])
            else:
                put('', 'trade', f'{pair}_buy', buy, str(trade_buy_no))

            balance = get(base_tick, 'balance', 0, buy[0])
            balance += dx
            assert balance >= 0
            put(addr, base_tick, 'balance', balance, buy[0])

            balance = get(quote_tick, 'balance', 0, addr)
            balance += dx * price // K
            assert balance >= 0
            put(addr, quote_tick, 'balance', balance, addr)

            base_value += dx
            assert base_value <= 0
            if base_value == 0:
                break

            if buy[4] is None:
                break
            trade_buy_no = buy[4]

        balance = get(base_tick, 'balance', 0, addr)
        balance -= base_value
        assert balance >= 0
        put(addr, base_tick, 'balance', balance, addr)

    elif base_value is None and quote_value < 0:
        balance = get(quote_tick, 'balance', 0, addr)
        # print('quote_tick balance', balance, quote_value, balance + quote_value)
        balance += quote_value
        assert balance >= 0
        put(addr, quote_tick, 'balance', balance, addr)

        trade_sell_no = trade_sell_start
        while True:
            sell = get('trade', f'{pair}_sell', None, str(trade_sell_no))
            if sell is None:
                break

            price = - sell[2] * K // sell[1]
            # dx = min(-sell[1], sell[2] * K // price, -quote_value)
            dx = min(-sell[1], -quote_value * K // price)
            sell[1] += dx
            sell[2] -= dx * price // K
            if sell[1] == 0 and sell[2] == 0:
                put('', 'trade', f'{pair}_sell', None, str(trade_sell_no))
                if sell[4] is None:
                    trade_sell_new = get('trade', f'{pair}_sell_new', 1)
                    put('', 'trade', f'{pair}_sell_start', trade_sell_new)
                else:
                    put('', 'trade', f'{pair}_sell_start', sell[4])
            else:
                put('', 'trade', f'{pair}_sell', sell, str(trade_sell_no))

            balance = get(base_tick, 'balance', 0, addr)
            balance += dx
            assert balance >= 0
            put(addr, base_tick, 'balance', balance, addr)

            balance = get(quote_tick, 'balance', 0, sell[0])
            balance += dx * price // K
            assert balance >= 0
            put(addr, quote_tick, 'balance', balance, sell[0])

            quote_value += dx * price // K
            assert quote_value <= 0
            if quote_value == 0:
                break

            if sell[4] is None:
                break
            trade_sell_no = sell[4]

        balance = get(quote_tick, 'balance', 0, addr)
        balance -= quote_value
        assert balance >= 0
        put(addr, quote_tick, 'balance', balance, addr)
