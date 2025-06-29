def token_create(info, args):
    assert args['f'] == 'token_create'
    sender = info['sender']
    handle = handle_lookup(sender)
    addr = handle or sender

    tick = args['a'][0]
    assert type(tick) is str
    assert len(tick) > 0 and len(tick) < 42
    assert tick[0] in string.ascii_uppercase
    assert set(tick) <= set(string.ascii_uppercase+string.digits+'_')

    name = args['a'][1]
    assert type(name) is str
    decimal = int(args['a'][2])
    assert type(decimal) is int
    assert decimal >= 0 and decimal <= 18

    functions = ['transfer', 'approve', 'transfer_from', 'token_mint_once', 'asset_update_ownership', 'asset_update_functions']
    if len(args['a']) == 4:
        functions = args['a'][3]
        assert type(functions) is list

    put(addr, tick, 'name', name)
    put(addr, tick, 'decimal', decimal)
    put(addr, 'asset', 'functions', functions, tick)
