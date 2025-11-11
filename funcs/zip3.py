def asset_create(info, args):
    assert args['f'] == 'asset_create'
    sender = info['sender']
    tick = args['a'][0]
    assert type(tick) is str
    assert len(tick) > 0 and len(tick) < 42
    assert tick[0] in string.ascii_uppercase
    assert set(tick) <= set(string.ascii_uppercase+string.digits+'_')
    addr = handle_lookup(sender)
    owner, _ = get('asset', 'owner', None, tick)
    assert not owner

    put(addr, 'asset', 'owner', addr, tick)
    put(addr, 'asset', 'functions', ['asset_update_ownership', 'asset_update_functions'], tick)

def asset_update_ownership(info, args):
    assert args['f'] == 'asset_update_ownership'
    sender = info['sender']
    tick = args['a'][0]
    receiver = args['a'][1]
    assert type(tick) is str
    assert len(tick) > 0 and len(tick) < 42
    assert tick[0] in string.ascii_uppercase
    assert set(tick) <= set(string.ascii_uppercase+string.digits+'_')
    addr = handle_lookup(sender)
    owner, _ = get('asset', 'owner', None, tick)
    assert owner == addr

    # DO THIS to change the owner using receiver's Zentra token
    functions, _ = get('asset', 'functions', None, tick)
    assert type(functions) is list
    assert functions
    put(receiver, 'asset', 'owner', receiver, tick)
    put(receiver, 'asset', 'functions', functions, tick)


def asset_update_functions(info, args):
    assert args['f'] == 'asset_update_functions'
    sender = info['sender']
    addr = handle_lookup(sender)

    tick = args['a'][0]
    assert type(tick) is str
    assert len(tick) > 0 and len(tick) < 42
    assert tick[0] in string.ascii_uppercase
    assert set(tick) <= set(string.ascii_uppercase+string.digits+'_')
    owner, _ = get('asset', 'owner', None, tick)
    assert owner == addr

    functions = args['a'][1]
    assert type(functions) is list
    assert functions
    put(addr, 'asset', 'functions', functions, tick)
