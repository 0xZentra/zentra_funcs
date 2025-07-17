
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
    if quote_value is None and int(base_value) < 0:
        base_value = int(args['a'][1])
        base_balance = get(base_tick, 'balance', 0, addr)

        trade_buy_no = trade_buy_start
        while True:
            buy = get('trade', f'{pair}_buy', None, str(trade_buy_no))
            if buy is None:
                break

            price = buy[3]
            dx_base = min(buy[1], -buy[2] * K // price, -base_value)
            dx_quote = dx_base * price // K
            if dx_base == 0 or dx_quote == 0:
                break
            buy[1] -= dx_base
            buy[2] += dx_quote

            if base_balance - dx_base < 0:
                break
            base_balance -= dx_base

            if buy[1] == 0 or buy[1] // price == 0:
                if buy[4]:
                    prev_buy = get('trade', f'{pair}_buy', None, str(buy[4]))
                    prev_buy[5] = buy[5]
                    put(prev_buy[0], 'trade', f'{pair}_buy', prev_buy, str(buy[4]))

                if buy[5]:
                    next_buy = get('trade', f'{pair}_buy', None, str(buy[5]))
                    next_buy[4] = buy[4]
                    put(next_buy[0], 'trade', f'{pair}_buy', next_buy, str(buy[5]))

                if buy[4] is not None and buy[5] is None:
                    trade_buy_start = buy[4]
                    put(addr, 'trade', f'{pair}_buy_start', trade_buy_start)
                elif buy[4] is None and buy[5] is None:
                    trade_buy_new = get('trade', f'{pair}_buy_new', 1)
                    trade_buy_start = trade_buy_new
                    put(addr, 'trade', f'{pair}_buy_start', trade_buy_start)

                if buy[2] < 0:
                    balance = get(quote_tick, 'balance', 0, buy[0])
                    balance -= buy[2]
                    assert balance >= 0
                    put(buy[0], quote_tick, 'balance', balance, buy[0])
    
                put(buy[0], 'trade', f'{pair}_buy', None, str(trade_buy_no))
            else:
                put(buy[0], 'trade', f'{pair}_buy', buy, str(trade_buy_no))

            base_value += dx_base
            assert base_value <= 0
            balance = get(quote_tick, 'balance', 0, addr)
            balance += dx_quote
            assert balance >= 0
            put(addr, quote_tick, 'balance', balance, addr)

            if buy[4] is None:
                break
            trade_buy_no = buy[4]

        assert base_balance >= 0
        put(addr, base_tick, 'balance', base_balance, addr)

    elif quote_value is None and int(base_value) > 0:
        base_value = int(args['a'][1])
        quote_balance = get(quote_tick, 'balance', 0, addr)

        trade_sell_no = trade_sell_start
        while True:
            sell = get('trade', f'{pair}_sell', None, str(trade_sell_no))
            if sell is None:
                break

            price = sell[3]
            dx_base = min(-sell[1], quote_balance * K // price, base_value)
            dx_quote = dx_base * price // K
            if dx_base == 0 or dx_quote == 0:
                break
            sell[1] += dx_base
            sell[2] -= dx_quote

            if quote_balance - dx_quote < 0:
                break
            quote_balance -= dx_quote

            if sell[1] == 0 or sell[1] // price == 0:
                if sell[4]:
                    prev_sell = get('trade', f'{pair}_sell', None, str(sell[4]))
                    prev_sell[5] = sell[5]
                    put(prev_sell[0], 'trade', f'{pair}_sell', prev_sell, str(sell[4]))

                if sell[5]:
                    next_sell = get('trade', f'{pair}_sell', None, str(sell[5]))
                    next_sell[4] = sell[4]
                    put(next_sell[0], 'trade', f'{pair}_sell', next_sell, str(sell[5]))

                if sell[4] is not None and sell[5] is None:
                    trade_sell_start = sell[4]
                    put(addr, 'trade', f'{pair}_sell_start', trade_sell_start)
                elif sell[4] is None and sell[5] is None:
                    trade_sell_new = get('trade', f'{pair}_sell_new', 1)
                    trade_sell_start = trade_sell_new
                    put(addr, 'trade', f'{pair}_sell_start', trade_sell_start)

                if sell[1] < 0:
                    balance = get(base_tick, 'balance', 0, sell[0])
                    balance -= sell[1]
                    assert balance >= 0
                    put(sell[0], base_tick, 'balance', balance, sell[0])

                put(sell[0], 'trade', f'{pair}_sell', None, str(trade_sell_no))
            else:
                put(sell[0], 'trade', f'{pair}_sell', sell, str(trade_sell_no))

            balance = get(quote_tick, 'balance', 0, sell[0])
            balance += dx_quote
            assert balance >= 0
            put(addr, quote_tick, 'balance', balance, sell[0])

            base_value -= dx_base
            assert base_value >= 0
            balance = get(base_tick, 'balance', 0, addr)
            balance += dx_base
            assert balance >= 0
            put(addr, base_tick, 'balance', balance, addr)

            if sell[4] is None:
                break
            trade_sell_no = sell[4]

        assert quote_balance >= 0
        put(addr, quote_tick, 'balance', quote_balance, addr)

    elif base_value is None and int(quote_value) < 0:
        quote_value = int(args['a'][3])
        quote_balance = get(quote_tick, 'balance', 0, addr)

        trade_sell_no = trade_sell_start
        while True:
            sell = get('trade', f'{pair}_sell', None, str(trade_sell_no))
            if sell is None:
                break

            price = sell[3]
            dx_base = min(-sell[1], -quote_value * K // price)
            dx_quote = dx_base * price // K
            if dx_base == 0 or  dx_quote == 0:
                break
            sell[1] += dx_base
            sell[2] -= dx_quote

            if quote_balance - dx_quote < 0:
                break
            quote_balance -= dx_quote

            if sell[1] == 0 or sell[1] // price == 0:
                if sell[4]:
                    prev_sell = get('trade', f'{pair}_sell', None, str(sell[4]))
                    prev_sell[5] = sell[5]
                    put(prev_sell[0], 'trade', f'{pair}_sell', prev_sell, str(sell[4]))

                if sell[5]:
                    next_sell = get('trade', f'{pair}_sell', None, str(sell[5]))
                    next_sell[4] = sell[4]
                    put(next_sell[0], 'trade', f'{pair}_sell', next_sell, str(sell[5]))

                if sell[4] is not None and sell[5] is None:
                    trade_sell_start = sell[4]
                    put(addr, 'trade', f'{pair}_sell_start', trade_sell_start)
                elif sell[4] is None and sell[5] is None:
                    trade_sell_new = get('trade', f'{pair}_sell_new', 1)
                    trade_sell_start = trade_sell_new
                    put(addr, 'trade', f'{pair}_sell_start', trade_sell_start)

                if sell[1] < 0:
                    balance = get(base_tick, 'balance', 0, sell[0])
                    balance -= sell[1]
                    assert balance >= 0
                    put(sell[0], base_tick, 'balance', balance, sell[0])

                put(sell[0], 'trade', f'{pair}_sell', None, str(trade_sell_no))
            else:
                put(sell[0], 'trade', f'{pair}_sell', sell, str(trade_sell_no))

            quote_value += dx_quote
            assert quote_value <= 0
            balance = get(base_tick, 'balance', 0, addr)
            balance += dx_base
            assert balance >= 0
            put(addr, base_tick, 'balance', balance, addr)

            if sell[4] is None:
                break
            trade_sell_no = sell[4]

        assert quote_balance >= 0
        put(addr, quote_tick, 'balance', quote_balance, addr)

    elif base_value is None and int(quote_value) > 0:
        # this is a sell, get USDC by selling BTC
        quote_value = int(args['a'][3])
        base_balance = get(base_tick, 'balance', 0, addr)

        trade_buy_no = trade_buy_start
        while True:
            buy = get('trade', f'{pair}_buy', None, str(trade_buy_no))
            if buy is None:
                break

            price = buy[3]
            dx_base = min(buy[1], base_balance, quote_value * K // price)
            dx_quote = dx_base * price // K
            if dx_base == 0 or dx_quote == 0:
                break
            buy[1] -= dx_base
            buy[2] += dx_quote

            if base_balance - dx_base < 0:
                break
            base_balance -= dx_base

            if buy[1] == 0 or buy[1] // price == 0:
                if buy[4]:
                    prev_buy = get('trade', f'{pair}_buy', None, str(buy[4]))
                    prev_buy[5] = buy[5]
                    put(prev_buy[0], 'trade', f'{pair}_buy', prev_buy, str(buy[4]))

                if buy[5]:
                    next_buy = get('trade', f'{pair}_buy', None, str(buy[5]))
                    next_buy[4] = buy[4]
                    put(next_buy[0], 'trade', f'{pair}_buy', next_buy, str(buy[5]))

                if buy[4] is not None and buy[5] is None:
                    trade_buy_start = buy[4]
                    put(addr, 'trade', f'{pair}_buy_start', trade_buy_start)
                elif buy[4] is None and buy[5] is None:
                    trade_buy_new = get('trade', f'{pair}_buy_new', 1)
                    trade_buy_start = trade_buy_new
                    put(addr, 'trade', f'{pair}_buy_start', trade_buy_start)

                if buy[2] < 0:
                    balance = get(quote_tick, 'balance', 0, buy[0])
                    balance -= buy[2]
                    assert balance >= 0
                    put(buy[0], quote_tick, 'balance', balance, buy[0])
    
                put(buy[0], 'trade', f'{pair}_buy', None, str(trade_buy_no))
            else:
                put(buy[0], 'trade', f'{pair}_buy', buy, str(trade_buy_no))

            balance = get(base_tick, 'balance', 0, buy[0])
            balance += dx_base
            assert balance >= 0
            put(addr, base_tick, 'balance', balance, buy[0])

            quote_value -= dx_quote
            assert quote_value >= 0
            balance = get(quote_tick, 'balance', 0, addr)
            balance += dx_quote
            assert balance >= 0
            put(addr, quote_tick, 'balance', balance, addr)

            if buy[4] is None:
                break
            trade_buy_no = buy[4]

        assert base_balance >= 0
        put(addr, base_tick, 'balance', base_balance, addr)
