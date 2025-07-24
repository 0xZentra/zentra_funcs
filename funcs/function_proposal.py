
def function_proposal(info, args):
    assert args['f'] == 'function_proposal'
    sender = info['sender']
    handle = handle_lookup(sender)
    addr = handle or sender
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

    hexdigest = hashlib.sha256(sourcecode.encode('utf8')).hexdigest()
    k = 'function-proposal-%s:%s' % (fname, hexdigest)
    put(addr, 'function', 'proposal', {
            'sourcecode': sourcecode,
            'require': require, 'votes': []
        }, '%s:%s' % (fname, hexdigest))

