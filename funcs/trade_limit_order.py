def trade_limit_order(info, args):
    assert args['f'] == 'trade_limit_order'
    sender = info['sender']
    handle = handle_lookup(sender)
    addr = handle or sender
    print('trade_limit_order addr', addr, 'handle', handle, 'sender', sender)

    base_tick = args['a'][0]
    quote_tick = args['a'][2]
    assert set(base_tick) <= set(string.ascii_uppercase+'_')
    assert set(quote_tick) <= set(string.ascii_uppercase+'_')
    # TODO: make sure quote_tick is set

    pair = '%s_%s' % tuple([base_tick, quote_tick])
    # TODO: check if pair exists

    base_value = int(args['a'][1])
    quote_value = int(args['a'][3])
    assert base_value * quote_value < 0
    K = 10**18

    trade_buy_start = get('trade', f'{pair}_buy_start', 1) # from maximum
    trade_buy_new = get('trade', f'{pair}_buy_new', 1)
    trade_sell_start = get('trade', f'{pair}_sell_start', 1) # from minimum
    trade_sell_new = get('trade', f'{pair}_sell_new', 1)

    # SORT AND INSERT
    if base_value < 0 and quote_value > 0: # sell token get USDC
        balance = get(base_tick, 'balance', 0, addr)
        # print('base_tick balance', balance, addr, base_tick)
        balance += base_value
        assert balance >= 0
        put(addr, base_tick, 'balance', balance, addr)

        trade_sell_no = trade_sell_start
        while True:
            sell = get('trade', f'{pair}_sell', None, str(trade_sell_no))
            price = - quote_value * K // base_value
            if sell is None:
                put(addr, 'trade', f'{pair}_sell', [addr, base_value, quote_value, price, None, None], str(trade_sell_new))
                trade_sell_new += 1
                put(addr, 'trade', f'{pair}_sell_new', trade_sell_new)
                break

            # print('sell prices', price, sell[3])
            if price < sell[3]:
                next_sell_id = sell[5]
                put(addr, 'trade', f'{pair}_sell', [addr, base_value, quote_value, price, trade_sell_no, next_sell_id], str(trade_sell_new))
                if next_sell_id is None:
                    trade_sell_start = trade_sell_new
                    put(addr, 'trade', f'{pair}_sell_start', trade_sell_start)
                sell[5] = trade_sell_new
                trade_sell_new += 1
                put(addr, 'trade', f'{pair}_sell_new', trade_sell_new)

                put(addr, 'trade', f'{pair}_sell', sell, str(trade_sell_no))
                if next_sell_id is not None:
                    next_sell = get('trade', f'{pair}_sell', None, str(next_sell_id))
                    if next_sell is not None:
                        next_sell[4] = sell[5]
                        put(addr, 'trade', f'{pair}_sell', next_sell, str(next_sell_id))
                break

            if sell[4] is None:
                put(addr, 'trade', f'{pair}_sell', [addr, base_value, quote_value, price, None, trade_sell_no], str(trade_sell_new))
                put(addr, 'trade', f'{pair}_sell', [sell[0], sell[1], sell[2], sell[3], trade_sell_new, sell[5]], str(trade_sell_no))
                trade_sell_new += 1
                put(addr, 'trade', f'{pair}_sell_new', trade_sell_new)
                break

            trade_sell_no = sell[4]

    elif base_value > 0 and quote_value < 0: # buy token with USDC
        balance = get(quote_tick, 'balance', 0, addr)
        balance += quote_value
        assert balance >= 0
        put(addr, quote_tick, 'balance', balance, addr)

        trade_buy_no = trade_buy_start
        while True:
            buy = get('trade', f'{pair}_buy', None, str(trade_buy_no))
            price = - quote_value * K // base_value
            if buy is None:
                buy = [addr, base_value, quote_value, price, None, None]
                put(addr, 'trade', f'{pair}_buy', buy, str(trade_buy_new))
                trade_buy_new += 1
                put(addr, 'trade', f'{pair}_buy_new', trade_buy_new)
                break

            # print('buy prices', price, buy[3])
            if price > buy[3]:
                # print('buy', buy)
                next_buy_id = buy[5]
                put(addr, 'trade', f'{pair}_buy', [addr, base_value, quote_value, price, trade_buy_no, next_buy_id], str(trade_buy_new))
                if next_buy_id is None:
                    trade_buy_start = trade_buy_new
                    put(addr, 'trade', f'{pair}_buy_start', trade_buy_start)
                buy[5] = trade_buy_new
                trade_buy_new += 1
                put(addr, 'trade', f'{pair}_buy_new', trade_buy_new)

                put(addr, 'trade', f'{pair}_buy', buy, str(trade_buy_no))
                if next_buy_id is not None:
                    next_buy = get('trade', f'{pair}_buy', None, str(next_buy_id))
                    if next_buy is not None:
                        next_buy[4] = buy[5]
                        put(addr, 'trade', f'{pair}_buy', next_buy, str(next_buy_id))
                break

            if buy[4] is None:
                put(addr, 'trade', f'{pair}_buy', [addr, base_value, quote_value, price, None, trade_buy_no], str(trade_buy_new))
                put(addr, 'trade', f'{pair}_buy', [buy[0], buy[1], buy[2], buy[3], trade_buy_new, buy[5]], str(trade_buy_no))
                trade_buy_new += 1
                put(addr, 'trade', f'{pair}_buy_new', trade_buy_new)
                break

            # print('trade_buy_no', trade_buy_no)
            trade_buy_no = buy[4]

    # MATCHING
    sell_to_refund = []
    buy_to_refund = []
    sell_to_remove = set([])
    # trade_buy_start = get('trade', f'{pair}_buy_start', 1)
    # trade_sell_start = get('trade', f'{pair}_sell_start', 1)
    # print('trade_buy_start', trade_buy_start, 'trade_sell_start', trade_sell_start)
    trade_sell_no = trade_sell_start
    highest_buy_price = None

    while True:
        sell = get('trade', f'{pair}_sell', None, str(trade_sell_no))
        if not sell:
            break
        # sell_price = - sell[2] * K // sell[1]
        sell_price = sell[3]
        # print('>sell_price', sell_price)
        if highest_buy_price and sell_price > highest_buy_price:
            # print('highest_buy_price', highest_buy_price)
            break
        buy_to_remove = set([])

        trade_buy_no = trade_buy_start
        while True:
            buy = get('trade', f'{pair}_buy', None, str(trade_buy_no))
            if not buy:
                break
            # buy_price = - buy[2] * K // buy[1]
            buy_price = buy[3]
            print('buy_price', buy_price)
            if highest_buy_price is None:
                highest_buy_price = buy_price
            if sell_price > buy_price:
                trade_buy_no = buy[4]
                continue

            # matched_price = (buy_price + sell_price) // 2
            matched_price = sell_price
            # dx = min(-sell[1], sell[2] * K // matched_price, buy[1])
            dx = min(-sell[1], buy[1])
            sell[1] += dx
            sell[2] -= dx * matched_price // K
            buy[1] -= dx
            buy[2] += dx * matched_price // K

            balance = get(base_tick, 'balance', 0, buy[0])
            balance += dx
            assert balance >= 0
            put(buy[0], base_tick, 'balance', balance, buy[0])

            balance = get(quote_tick, 'balance', 0, sell[0])
            balance += dx * matched_price // K
            assert balance >= 0
            put(sell[0], quote_tick, 'balance', balance, sell[0])

            if buy[1] == 0:
                buy_to_remove.add(trade_buy_no)

                if buy[2] != 0:
                    buy_to_refund.append(buy)
            else:
                put('', 'trade', f'{pair}_buy', buy, str(trade_buy_no))

            if sell[1] == 0:
                break
            if buy[4] is None:
                break
            trade_buy_no = buy[4]

        for i in buy_to_remove:
            put('', 'trade', f'{pair}_buy', None, str(i))

        if sell[1] == 0:
            sell_to_remove.add(trade_sell_no)
            if sell[4]:
                prev_sell = get('trade', f'{pair}_sell', None, str(sell[4]))
                prev_sell[5] = None
                put('', 'trade', f'{pair}_sell', prev_sell, str(sell[4]))
            trade_sell_start = sell[4] or trade_sell_new

            if sell[2] > 0:
                sell_to_refund.append(sell)
        else:
            put('', 'trade', f'{pair}_sell', sell, str(trade_sell_no))

        if sell[4] is None:
            break
        trade_sell_no = sell[4]

    for i in sell_to_remove:
        put('', 'trade', f'{pair}_sell', None, str(i))
    put('', 'trade', f'{pair}_sell_start', trade_sell_start)
    put('', 'trade', f'{pair}_buy_start', trade_buy_start)

    for i in buy_to_refund:
        balance = get(quote_tick, 'balance', 0, i[0])
        balance -= i[2]
        assert balance >= 0
        put(i[0], quote_tick, 'balance', balance, i[0])

    # for i in sell_to_refund:
    #     print(f'{pair}_sell_to_refund', i)
