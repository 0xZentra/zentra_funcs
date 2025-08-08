def function_snippet(info, args):
    assert args['f'] == 'function_snippet'
    sender = info['sender']
    addr = handle_lookup(sender)
    snippet = args['a'][0]
    snippet_digest = hashlib.sha256(snippet.encode('utf8')).hexdigest()
    put(addr, 'function', 'snippet', {
        'snippet': snippet,
        'functions': []
        }, snippet_digest)
    event('NewFunctionSnippet', [snippet_digest])


def function_snippet_clear(info, args):
    assert args['f'] == 'function_snippet_clear'
    sender = info['sender']
    addr = handle_lookup(sender)
    snippet_digest = args['a'][0]
    snippet, _ = get('function', 'snippet', None, snippet_digest)
    assert snippet, "Snippet not found: %s" % snippet_digest
    assert snippet['functions'] == [], "Snippet is not empty: %s" % snippet
    put(addr, 'function', 'snippet', None, snippet_digest)
    event('RemoveFunctionSnippet', [snippet_digest, True])


def function_proposal(info, args):
    assert args['f'] == 'function_proposal'
    sender = info['sender']
    addr = handle_lookup(sender)
    func_names = args['a'][0]
    snippet_digests = args['a'][1]
    for func_name in func_names:
        assert set(func_name) <= set(string.ascii_lowercase+'_')
        assert not func_name.startswith('_')

    snippet_digests = args['a'][1]
    for snippet_digest in snippet_digests:
        assert set(snippet_digest) <= set(string.ascii_lowercase+string.digits)
        assert len(snippet_digest) == 64

    proposal_id, _ = get('function', 'proposal_count', 0)
    proposal_id += 1
    put(addr, 'function', 'proposal_count', proposal_id)

    put(addr, 'function', 'proposal', {
            'functions': func_names,
            'snippets': snippet_digests,
            'votes': []
        }, '%s' % (proposal_id))
    event('FunctionProposal', [proposal_id, func_names])


def function_vote(info, args):
    assert args['f'] == 'function_vote'
    sender = info['sender']
    addr = handle_lookup(sender)
    committee_members, _ = get('committee', 'members', [])
    committee_members = set(committee_members)
    assert addr in committee_members

    proposal_id = args['a'][0]
    proposal, _ = get('function', 'proposal', None, '%s' % proposal_id)
    assert proposal
    votes = set(proposal['votes'])
    votes.add(addr)
    proposal['votes'] = list(votes)

    if len(votes) >= len(committee_members)*2//3:
        assert len(proposal['snippets']) > 0
        for snippet_hash in proposal['snippets']:
            assert set(snippet_hash) <= set(string.ascii_lowercase+string.digits)
            snippet, _ = get('function', 'snippet', None, snippet_hash)
            assert snippet, "Snippet not found: %s" % snippet_hash
            snippet['functions'].extend(proposal['functions'])
            put('', 'function', 'snippet', snippet, snippet_hash)

        assert len(proposal['functions']) > 0
        for func_name in proposal['functions']:
            put(addr, 'function', 'code', {
                'snippets': proposal['snippets']
            }, func_name)
        event('NewFunctions', [proposal_id, proposal['functions']])
    else:
        put(addr, 'function', 'proposal', proposal, '%s' % proposal_id)
        event('FunctionVote', [proposal_id, addr])
