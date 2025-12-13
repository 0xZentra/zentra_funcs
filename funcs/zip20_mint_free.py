
def token_mint_free(info, args):
    tick = args['a'][0]
    assert type(tick) is str
    assert len(tick) > 0 and len(tick) < 42
    assert tick[0] in string.ascii_uppercase
    assert set(tick) <= set(string.ascii_uppercase+string.digits+'_')

    assert args['f'] == 'token_mint_free'
    functions, _ = get('asset', 'functions', [], tick)
    assert args['f'] in functions

    value = int(args['a'][1])
    assert value > 0

    sender = info['sender']
    addr = handle_lookup(sender)

    balance, _ = get(tick, 'balance', 0, addr)
    balance += value
    put(addr, tick, 'balance', balance, addr)

    total, _ = get(tick, 'total', 0)
    total += value
    put(addr, tick, 'total', total)
    event('TokenMintedFree', [tick, value, total])

