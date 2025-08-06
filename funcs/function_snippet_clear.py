
def function_snippet_clear(info, args):
    assert args['f'] == 'function_snippet_clear'
    sender = info['sender']
    handle = handle_lookup(sender)
    addr = handle or sender
    snippet_digest = args['a'][0]
    snippet = get('function', 'snippet', None, snippet_digest)
    assert snippet, "Snippet not found: %s" % snippet_digest
    assert snippet['functions'] == [], "Snippet is not empty: %s" % snippet
    put(addr, 'function', 'snippet', None, snippet_digest)
    event('RemoveFunctionSnippet', [snippet_digest, True])
