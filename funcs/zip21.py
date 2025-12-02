def bridge_incoming(info, args):
    tick = args['a'][0]
    assert type(tick) is str
    assert len(tick) > 0 and len(tick) < 42
    assert tick[0] in string.ascii_uppercase
    assert set(tick) <= set(string.ascii_uppercase+string.digits+'_')

    assert args['f'] == 'bridge_incoming'
    functions, _ = get('asset', 'functions', [], tick)
    assert args['f'] in functions

    operator, _ = get(tick, 'bridge_operator', None)
    assert operator is not None, "Bridge is not initialized"
    sender = info['sender']
    assert sender == operator, "Only the operator can perform this operation"

    amount = int(args['a'][1])
    assert amount > 0

    receiver = args['a'][2].lower()
    assert len(receiver) <= 42
    assert type(receiver) is str
    if len(receiver) == 42:
        assert receiver.startswith('0x')
        assert set(receiver[2:]) <= set(string.digits+'abcdef')
    else:
        assert len(receiver) > 4

    chain = args['a'][3].lower()
    assert chain in ['base']
    tx_hash = args['a'][4].lower().replace('0x', '')
    assert len(tx_hash) == 64

    balance, _ = get(tick, 'balance', 0, receiver)
    balance = int(balance)
    balance += amount
    put(receiver, tick, 'balance', balance, receiver)

    total, _ = get(tick, 'total', 0)
    total = int(total)
    total += amount
    asset_owner, _ = get('asset', 'owner', None, tick)
    assert asset_owner
    put(asset_owner, tick, 'total', total)

    event('BridgeIn', [tick, amount, receiver, chain, tx_hash])


def bridge_outgoing(info, args):
    tick = args['a'][0]
    assert type(tick) is str
    assert len(tick) > 0 and len(tick) < 42
    assert tick[0] in string.ascii_uppercase
    assert set(tick) <= set(string.ascii_uppercase+string.digits+'_')

    assert args['f'] == 'bridge_outgoing'
    functions, _ = get('asset', 'functions', [], tick)
    assert args['f'] in functions

    amount = int(args['a'][1])
    assert amount > 0

    sender = info['sender']
    addr = handle_lookup(sender)

    balance, _ = get(tick, 'balance', 0, addr)
    balance = int(balance)
    assert balance - amount >= 0
    balance -= amount
    put(addr, tick, 'balance', balance, addr)

    total, _ = get(tick, 'total', 0)
    total = int(total)
    assert total - amount >= 0
    total -= amount
    asset_owner, _ = get('asset', 'owner', None, tick)
    assert asset_owner
    put(asset_owner, tick, 'total', total)

    chain = args['a'][2]
    assert chain in ['base']

    event('BridgeOut', [tick, amount, sender, chain])


def bridge_set_operator(info, args):
    tick = args['a'][0]
    assert type(tick) is str
    assert len(tick) > 0 and len(tick) < 42
    assert tick[0] in string.ascii_uppercase
    assert set(tick) <= set(string.ascii_uppercase+string.digits+'_')

    assert args['f'] == 'bridge_set_operator'
    functions, _ = get('asset', 'functions', [], tick)
    assert args['f'] in functions

    asset_owner, _ = get('asset', 'owner', None, tick)
    sender = info['sender']
    addr = handle_lookup(sender)
    # print('bridge_set_operator', asset_owner, addr)
    assert sender == asset_owner, "Only the asset owner can perform this operation"

    operator = args['a'][1].lower()
    assert type(operator) is str
    # assert len(operator) == 42
    assert operator.startswith('0x')
    assert set(operator[2:]) <= set(string.digits+'abcdef')

    put(addr, tick, 'bridge_operator', operator)
    event('BridgeOperaterSet', [tick, operator])


def bridge_unset_operator(info, args):
    tick = args['a'][0]
    assert type(tick) is str
    assert len(tick) > 0 and len(tick) < 42
    assert tick[0] in string.ascii_uppercase
    assert set(tick) <= set(string.ascii_uppercase+string.digits+'_')

    assert args['f'] == 'bridge_unset_operator'
    functions, _ = get('asset', 'functions', [], tick)
    assert args['f'] in functions

    asset_owner, _ = get('asset', 'owner', None, tick)
    sender = info['sender']
    addr = handle_lookup(sender)
    assert addr == asset_owner, "Only the asset owner can perform this operation"

    put(addr, tick, 'bridge_operator', None)
    event('BridgeOperaterUnset', [tick])

def bridge_set_outgoing_fee(info, args):
    tick = args['a'][0]
    assert type(tick) is str
    assert len(tick) > 0 and len(tick) < 42
    assert tick[0] in string.ascii_uppercase
    assert set(tick) <= set(string.ascii_uppercase+string.digits+'_')

    assert args['f'] == 'bridge_set_outgoing_fee'
    functions, _ = get('asset', 'functions', [], tick)
    assert args['f'] in functions

    chain = args['a'][1]
    assert chain in ['base']

    fee = int(args['a'][2])
    assert fee > 0

    asset_owner, _ = get('asset', 'owner', None, tick)
    sender = info['sender']
    addr = handle_lookup(sender)
    assert addr == asset_owner, "Only the asset owner can perform this operation"

    put(asset_owner, tick, 'bridgeout_fee', fee)
    event('BridgeOutFeeChanged', [tick, fee])
