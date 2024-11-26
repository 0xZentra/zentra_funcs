
def function_proposal(info, args):
    assert args['f'] == 'function_proposal'
    sender = info['sender'].lower()
    handle = handle_lookup(sender)
    fname = args['a'][0]
    assert set(fname) <= set(string.ascii_lowercase+'_')
    sourcecode = args['a'][1]

    require = args['a'][2]
    for i in require:
        assert type(i) is list
        assert set(i[0]) <= set(string.ascii_lowercase+'_')
        assert type(i[1]) is list
        for j in i[1]:
            assert set(j) <= set(string.ascii_uppercase+'_')

    asset_permission = args['a'][3]
    assert type(asset_permission) is list
    for i in asset_permission:
        assert i == '*' or set(i) <= set(string.ascii_lowercase+'_')

    invoke_permission = args['a'][4]
    assert type(invoke_permission) is list
    for i in invoke_permission:
        assert i == '*' or set(i) <= set(string.ascii_lowercase+'_')

    hexdigest = hashlib.sha256(sourcecode.encode('utf8')).hexdigest()
    k = 'function-proposal-%s:%s' % (fname, hexdigest)
    put(handle, 'function', 'proposal', {'sourcecode': sourcecode, 'asset_permission': asset_permission, 'require': require, 'votes': []}, '%s:%s' % (fname, hexdigest))
