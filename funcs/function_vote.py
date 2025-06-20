
def function_vote(info, args):
    assert args['f'] == 'function_vote'
    sender = info['sender']
    handle = handle_lookup(sender)
    addr = handle or sender
    committee_members = set(get('committee', 'members', []))
    assert addr in committee_members

    fname = args['a'][0]
    sourcecode_hexdigest = args['a'][1]
    proposal = get('function', 'proposal', None, '%s:%s' % (fname, sourcecode_hexdigest))
    votes = set(proposal['votes'])
    votes.add(addr)
    proposal['votes'] = list(votes)

    if len(votes) >= len(committee_members)*2//3:
        put(addr, 'function', 'code', proposal, fname)
    else:
        put(addr, 'function', 'proposal', proposal, '%s:%s' % (fname, sourcecode_hexdigest))
