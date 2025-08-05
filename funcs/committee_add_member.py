
def committee_add_member(info, args):
    assert args['f'] == 'committee_add_member'
    sender = info['sender']
    handle = handle_lookup(sender)
    addr = handle or sender
    committee_members = set(get('committee', 'members', []))
    assert addr in committee_members

    user = args['a'][0]
    votes = set(get('committee', 'proposal_add', [], user))
    votes.add(addr)
    votes = list(votes)

    if len(votes) >= len(committee_members) * 2 // 3:
        committee_members.add(user)
        put(addr, 'committee', 'members', list(committee_members))
        votes = None
    put(addr, 'committee', 'proposal_add', votes, user)
