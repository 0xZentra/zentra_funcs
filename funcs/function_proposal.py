
def function_proposal(info, args):
    assert args['f'] == 'function_proposal'
    sender = info['sender']
    handle = handle_lookup(sender)
    addr = handle or sender
    func_names = args['a'][0]
    snippet_digests = args['a'][1]
    for func_name in func_names:
        assert set(func_name) <= set(string.ascii_lowercase+'_')
        assert not func_name.startswith('_')

    snippet_digests = args['a'][1]
    for snippet_digest in snippet_digests:
        assert set(snippet_digest) <= set(string.ascii_lowercase+string.digits)
        assert len(snippet_digest) == 64

    proposal_id = get('function', 'proposal_count', 0)
    proposal_id += 1
    put(addr, 'function', 'proposal_count', proposal_id)

    put(addr, 'function', 'proposal', {
            'functions': func_names,
            'snippets': snippet_digests,
            'votes': []
        }, '%s' % (proposal_id))
    event('FunctionProposal', [proposal_id, func_names])
