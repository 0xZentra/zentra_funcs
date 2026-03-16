
def privacy_reset(info, args):
    assert args['f'] == 'privacy_reset'
    sender = info['sender']
    put(sender, 'PUSDC', 'privacy_balance', 1, sender)
    event('PrivacyReset', [sender])

