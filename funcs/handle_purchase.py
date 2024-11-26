
def handle_purchase(info, args):
    assert args['f'] == 'handle_purchase'
    sender = info['sender'].lower()
    handle = args['a'][0]
    assert type(handle) is str
    assert set(handle) <= set(string.digits+string.ascii_lowercase+'_')
    assert len(handle) > 4 and len(handle) < 42

    addr_existing = global_state.get(('zen-handle-handle2addr:%s' % (handle, )).encode('utf8'))
    if not addr_existing:
        global_state.put(('zen-handle-handle2addr:%s' % (handle, )).encode('utf8'), sender.encode('utf8'))
        handles = get('handle', 'addr2handles', [], sender)
        if handle not in handles:
            handles.append(handle)
            put(sender, 'handle', 'addr2handles', handles, sender)
            handle_existing = global_state.get(('zen-handle-addr2handle:%s' % (sender, )).encode('utf8'))
            if not handle_existing:
                global_state.put(('zen-handle-addr2handle:%s' % (sender, )).encode('utf8'), handle.encode('utf8'))
