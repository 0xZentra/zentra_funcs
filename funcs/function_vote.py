
def function_vote(info, args):
    assert args['f'] == 'function_vote'
    sender = info['sender']
    handle = handle_lookup(sender)
    addr = handle or sender
    committee_members = set(get('committee', 'members', []))
    assert addr in committee_members

    proposal_id = args['a'][0]
    proposal = get('function', 'proposal', None, '%s' % proposal_id)
    assert proposal
    votes = set(proposal['votes'])
    votes.add(addr)
    proposal['votes'] = list(votes)

    # print(len(votes), len(committee_members), len(committee_members)*2//3)
    if len(votes) >= len(committee_members)*2//3:
        assert len(proposal['snippets']) > 0
        for snippet_hash in proposal['snippets']:
            assert set(snippet_hash) <= set(string.ascii_lowercase+string.digits)
            snippet = get('function', 'snippet', None, snippet_hash)
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
