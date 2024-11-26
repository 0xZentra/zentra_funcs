
def committee_add_member(info, args):
    assert args['f'] == 'committee_add_member'
    sender = info['sender']
    handle = handle_lookup(sender)
    committee_members = set(get('committee', 'members', []))
    assert handle in committee_members

    user = args['a'][0]
    votes = set(get('committee', 'proposal', [], user))
    votes.add(handle)

    if len(votes) >= len(committee_members)*2//3:
        committee_members.add(user)
        put(handle, 'committee', 'members', list(committee_members))
    else:
        put(handle, 'committee', 'proposal', list(votes), user)
