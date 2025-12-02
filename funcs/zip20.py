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
    event('TokenCreated', [tick, name, decimal, functions])


def token_mint_once(info, args):
    tick = args['a'][0]
    assert type(tick) is str
    assert len(tick) > 0 and len(tick) < 42
    assert tick[0] in string.ascii_uppercase
    assert set(tick) <= set(string.ascii_uppercase+string.digits+'_')

    assert args['f'] == 'token_mint_once'
    functions, _ = get('asset', 'functions', [], tick)
    assert args['f'] in functions

    value = int(args['a'][1])
    assert value > 0

    sender = info['sender']
    addr = handle_lookup(sender)

    total, _ = get(tick, 'total', None)
    assert total is None, "Token already minted"
    put(addr, tick, 'total', value)

    balance, _ = get(tick, 'balance', 0, addr)
    balance += value
    put(addr, tick, 'balance', balance, addr)
    event('TokenMintedOnce', [tick, total])


def token_mint(info, args):
    tick = args['a'][0]
    assert type(tick) is str
    assert len(tick) > 0 and len(tick) < 42
    assert tick[0] in string.ascii_uppercase
    assert set(tick) <= set(string.ascii_uppercase+string.digits+'_')

    assert args['f'] == 'token_mint'
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
    event('TokenMinted', [tick, value, total])


def token_burn(info, args):
    tick = args['a'][0]
    assert type(tick) is str
    assert len(tick) > 0 and len(tick) < 42
    assert tick[0] in string.ascii_uppercase
    assert set(tick) <= set(string.ascii_uppercase+string.digits+'_')

    assert args['f'] == 'token_burn'
    functions, _ = get('asset', 'functions', [], tick)
    assert args['f'] in functions

    value = int(args['a'][1])
    assert value > 0
    sender = info['sender']
    addr = handle_lookup(sender)

    balance, _ = get(tick, 'balance', 0, addr)
    balance -= value
    assert balance >= 0

    total, _ = get(tick, 'total', 0, addr)
    total -= value
    assert total >= 0

    put(addr, tick, 'balance', balance, addr)
    put(addr, tick, 'total', total)
    event('TokenBurned', [tick, value, total])


def token_transfer(info, args):
    tick = args['a'][0]
    assert type(tick) is str
    assert len(tick) > 0 and len(tick) < 42
    assert tick[0] in string.ascii_uppercase
    assert set(tick) <= set(string.ascii_uppercase+string.digits+'_')

    assert args['f'] == 'token_transfer'
    functions, _ = get('asset', 'functions', [], tick)
    assert args['f'] in functions

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
    event('TokenTransfer', [tick, addr, receiver, value])


def token_send(info, args):
    tick = args['a'][0]
    assert type(tick) is str
    assert len(tick) > 0 and len(tick) < 42
    assert tick[0] in string.ascii_uppercase
    assert set(tick) <= set(string.ascii_uppercase+string.digits+'_')

    assert args['f'] == 'token_send'
    functions, _ = get('asset', 'functions', [], tick)
    assert args['f'] in functions

    sender = info['sender']
    addr = handle_lookup(sender)

    spender = args['a'][1].lower()  # the address allowed to spend
    assert len(spender) <= 42
    assert type(spender) is str
    if len(spender) == 42:
        assert spender.startswith('0x')
        assert set(spender[2:]) <= set(string.digits+'abcdef')
    else:
        assert len(spender) > 4

    value = int(args['a'][2])
    assert value >= 0

    put(addr, tick, 'allowance', value, f'{addr},{spender}')
    event('TokenSendApproval', [tick, addr, spender, value])


def token_accept(info, args):
    tick = args['a'][0]
    assert type(tick) is str
    assert len(tick) > 0 and len(tick) < 42
    assert tick[0] in string.ascii_uppercase
    assert set(tick) <= set(string.ascii_uppercase+string.digits+'_')

    assert args['f'] == 'token_accept'
    functions, _ = get('asset', 'functions', [], tick)
    assert args['f'] in functions

    from_addr = args['a'][1].lower()  # the address from which tokens are withdrawn
    assert len(from_addr) <= 42
    assert type(from_addr) is str
    if len(from_addr) == 42:
        assert from_addr.startswith('0x')
        assert set(from_addr[2:]) <= set(string.digits+'abcdef')
    else:
        assert len(from_addr) > 4

    to_addr = info['sender']
    to_addr = handle_lookup(to_addr)
    value = int(args['a'][2])
    assert value > 0

    allowance, _ = get(tick, 'allowance', 0, f'{from_addr},{to_addr}')
    from_balance, _ = get(tick, 'balance', 0, from_addr)
    allowance -= value
    assert allowance >= 0
    from_balance -= value
    assert from_balance >= 0
    put(from_addr, tick, 'allowance', allowance, f'{from_addr},{to_addr}')
    put(from_addr, tick, 'balance', from_balance, from_addr)

    to_balance, _ = get(tick, 'balance', 0, to_addr)
    to_balance += value
    put(to_addr, tick, 'balance', to_balance, to_addr)

    event('TokenSent', [tick, from_addr, to_addr, value])

