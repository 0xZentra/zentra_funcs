def committee_init(info, args):
    assert args['f'] == 'committee_init'
    sender = info['sender']
    addr = handle_lookup(sender)
    committee_members, _ = get('committee', 'members', [])
    assert not committee_members
    put(addr, 'committee', 'members', [addr])
    event('CommitteeInit', [addr])


def committee_add_member(info, args):
    assert args['f'] == 'committee_add_member'
    sender = info['sender']
    addr = handle_lookup(sender)
    committee_members, _ = get('committee', 'members', [])
    committee_members = set(committee_members)
    assert addr in committee_members

    user = args['a'][0]
    votes, _ = get('committee', 'proposal_add', [], user)
    votes = set(votes)
    votes.add(addr)
    votes = list(votes)
    event('CommitteeAddVote', [user, addr])

    if len(votes) >= len(committee_members) * 2 // 3:
        committee_members.add(user)
        put(addr, 'committee', 'members', list(committee_members))
        event('CommitteeAddMember', [user])
        votes = None
    put(addr, 'committee', 'proposal_add', votes, user)


def committee_remove_member(info, args):
    assert args['f'] == 'committee_remove_member'
    sender = info['sender']
    addr = handle_lookup(sender)
    committee_members, _ = get('committee', 'members', [])
    committee_members = set(committee_members)
    assert addr in committee_members

    user = args['a'][0]
    votes, _ = get('committee', 'proposal_remove', [], user)
    votes = set(votes)
    votes.add(addr)
    votes = list(votes)
    event('CommitteeRemoveVote', [user, addr])

    if len(votes) >= len(committee_members)*2//3:
        committee_members.remove(user)
        put(addr, 'committee', 'members', list(committee_members))
        event('CommitteeRemoveMember', [user])
        votes = None
    put(addr, 'committee', 'proposal_remove', votes, user)
