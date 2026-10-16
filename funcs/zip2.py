def function_snippet(info, args):
    assert args['f'] == 'function_snippet'
    sender = info['sender']
    addr = handle_lookup(sender)
    snippet = args['a'][0]
    snippet_digest = hashlib.sha256(snippet.encode('utf8')).hexdigest()
    existing, _ = get('function', 'snippet', None, snippet_digest)
    if existing:
        # Already published (content-addressed by digest); keep its bindings.
        return
    put(addr, 'function', 'snippet', {
        'snippet': snippet,
        'functions': []
        }, snippet_digest)
    event('NewFunctionSnippet', [snippet_digest])


def function_snippet_clear(info, args):
    assert args['f'] == 'function_snippet_clear'
    snippet_digest = args['a'][0]
    snippet, snippet_owner = get('function', 'snippet', None, snippet_digest)
    assert snippet, "Snippet not found: %s" % snippet_digest
    assert snippet['functions'] == [], "Snippet is not empty: %s" % snippet
    put(snippet_owner, 'function', 'snippet', None, snippet_digest)
    event('RemoveFunctionSnippet', [snippet_digest])


def function_proposal(info, args):
    assert args['f'] == 'function_proposal'
    sender = info['sender']
    addr = handle_lookup(sender)
    func_names = args['a'][0]
    snippet_digests = args['a'][1]
    for func_name in func_names:
        assert set(func_name) <= set(string.ascii_lowercase+string.digits+'_')
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

    # print(len(votes), len(committee_members), len(committee_members)*2//3)
    if len(votes) >= len(committee_members)*2//3:
        assert len(proposal['snippets']) > 0
        for snippet_hash in proposal['snippets']:
            assert set(snippet_hash) <= set(string.ascii_lowercase+string.digits)
            snippet, snippet_owner = get('function', 'snippet', None, snippet_hash)
            assert snippet, "Snippet not found: %s" % snippet_hash
            functions = snippet['functions']
            functions.extend(proposal['functions'])
            snippet['functions'] = list(set(functions))
            put(snippet_owner, 'function', 'snippet', snippet, snippet_hash)

        assert len(proposal['functions']) > 0
        for func_name in proposal['functions']:
            # Unbind the function from any snippet it was previously bound to
            # (other than the ones in this proposal). This leaves the old
            # snippet empty so it can be safely cleared later instead of
            # occupying global state forever.
            old_code, _ = get('function', 'code', None, func_name)
            if old_code:
                for old_hash in old_code.get('snippets', []):
                    if old_hash in proposal['snippets']:
                        continue
                    old_snippet, old_snippet_owner = get('function', 'snippet', None, old_hash)
                    if not old_snippet:
                        continue
                    functions = old_snippet['functions']
                    if func_name in functions:
                        functions.remove(func_name)
                    old_snippet['functions'] = functions
                    put(old_snippet_owner, 'function', 'snippet', old_snippet, old_hash)

            put(addr, 'function', 'code', {
                'snippets': proposal['snippets']
            }, func_name)

        event('NewFunctions', [proposal_id, proposal['functions']])
        funcs_reload(proposal['functions'])
    else:
        put(addr, 'function', 'proposal', proposal, '%s' % proposal_id)
        event('FunctionVote', [proposal_id, addr])


def function_delete_proposal(info, args):
    assert args['f'] == 'function_delete_proposal'
    sender = info['sender']
    addr = handle_lookup(sender)
    func_names = args['a'][0]
    for func_name in func_names:
        assert set(func_name) <= set(string.ascii_lowercase+string.digits+'_')
        assert not func_name.startswith('_')
        code, _ = get('function', 'code', None, func_name)
        assert code, "Function not found: %s" % func_name

    proposal_id, _ = get('function', 'delete_proposal_count', 0)
    proposal_id += 1
    put(addr, 'function', 'delete_proposal_count', proposal_id)

    put(addr, 'function', 'delete_proposal', {
            'functions': func_names,
            'votes': []
        }, '%s' % (proposal_id))
    event('FunctionDeleteProposal', [proposal_id, func_names])


def function_delete_vote(info, args):
    assert args['f'] == 'function_delete_vote'
    sender = info['sender']
    addr = handle_lookup(sender)
    committee_members, _ = get('committee', 'members', [])
    committee_members = set(committee_members)
    assert addr in committee_members

    proposal_id = args['a'][0]
    proposal, _ = get('function', 'delete_proposal', None, '%s' % proposal_id)
    assert proposal
    votes = set(proposal['votes'])
    votes.add(addr)
    proposal['votes'] = list(votes)

    if len(votes) >= len(committee_members)*2//3:
        assert len(proposal['functions']) > 0
        for func_name in proposal['functions']:
            code, _ = get('function', 'code', None, func_name)
            if code:
                for snippet_hash in code.get('snippets', []):
                    snippet, snippet_owner = get('function', 'snippet', None, snippet_hash)
                    if not snippet:
                        continue
                    functions = snippet['functions']
                    if func_name in functions:
                        functions.remove(func_name)
                    snippet['functions'] = functions
                    if functions:
                        put(snippet_owner, 'function', 'snippet', snippet, snippet_hash)
                    else:
                        put(snippet_owner, 'function', 'snippet', None, snippet_hash)
                        event('RemoveFunctionSnippet', [snippet_hash])
            put(addr, 'function', 'code', None, func_name)

        event('RemoveFunctions', [proposal_id, proposal['functions']])
        funcs_reload(proposal['functions'])
    else:
        put(addr, 'function', 'delete_proposal', proposal, '%s' % proposal_id)
        event('FunctionDeleteVote', [proposal_id, addr])

