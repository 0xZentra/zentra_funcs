def token_create(info, args):
    assert args['f'] == 'token_create'
    sender = info['sender']
    addr = handle_lookup(sender)

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

    functions = ['token_transfer', 'token_mint_once', 'asset_update_ownership', 'asset_update_functions']
    if len(args['a']) == 4:
        functions = args['a'][3]
        assert type(functions) is list

    put(addr, tick, 'name', name)
    put(addr, tick, 'decimal', decimal)
    put(addr, 'asset', 'functions', functions, tick)


def token_mint_once(info, args):
    tick = args['a'][0]
    assert type(tick) is str
    assert len(tick) > 0 and len(tick) < 42
    assert tick[0] in string.ascii_uppercase
    assert set(tick) <= set(string.ascii_uppercase+string.digits+'_')

    value = int(args['a'][1])
    assert value > 0

    assert args['f'] == 'token_mint_once'
    functions, _ = get('asset', 'functions', [], tick)
    assert args['f'] in functions

    sender = info['sender']
    addr = handle_lookup(sender)

    total, _ = get(tick, 'total', None)
    assert total is None, "Token already minted"
    put(addr, tick, 'total', value)

    balance, _ = get(tick, 'balance', 0, addr)
    balance += value
    put(addr, tick, 'balance', balance, addr)


def token_mint(info, args):
    tick = args['a'][0]
    assert type(tick) is str
    assert len(tick) > 0 and len(tick) < 42
    assert tick[0] in string.ascii_uppercase
    assert set(tick) <= set(string.ascii_uppercase+string.digits+'_')
    assert args['f'] == 'token_mint'

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


def token_burn(info, args):
    tick = args['a'][0]
    assert type(tick) is str
    assert len(tick) > 0 and len(tick) < 42
    assert tick[0] in string.ascii_uppercase
    assert set(tick) <= set(string.ascii_uppercase+string.digits+'_')

    assert args['f'] == 'token_burn'
    assert args['f'] in get('asset', 'functions', [], tick)

    value = int(args['a'][1])
    assert value > 0
    sender = info['sender']
    addr = handle_lookup(sender)

    balance = get(tick, 'balance', 0, addr)
    balance -= value
    assert balance >= 0

    total = get(tick, 'total', 0, addr)
    total -= value
    assert total >= 0

    put(addr, tick, 'balance', balance, addr)
    put(addr, tick, 'total', total)


def token_transfer(info, args):
    tick = args['a'][0]
    assert set(tick) <= set(string.ascii_uppercase+'_')

    assert args['f'] == 'token_transfer'
    assert args['f'] in get('asset', 'functions', [], tick)

    receiver = args['a'][1].lower()
    assert len(receiver) <= 42
    assert type(receiver) is str
    if len(receiver) == 42:
        assert receiver.startswith('0x')
        assert set(receiver[2:]) <= set(string.digits+'abcdef')
    else:
        assert len(receiver) > 4

    sender = info['sender']
    addr = handle_lookup(sender)

    value = int(args['a'][2])
    assert value > 0

    sender_balance, _ = get(tick, 'balance', 0, addr)
    assert sender_balance >= value
    sender_balance -= value
    put(addr, tick, 'balance', sender_balance, addr)
    receiver_balance, _ = get(tick, 'balance', 0, receiver)
    receiver_balance += value
    put(receiver, tick, 'balance', receiver_balance, receiver)
    event('Transfer', [tick, addr, receiver, value])


def token_send(info, args):
    assert args['f'] == 'token_send'


def token_accept(info, args):
    assert args['f'] == 'token_accept'
