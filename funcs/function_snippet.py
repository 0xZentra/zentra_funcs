
def function_snippet(info, args):
    assert args['f'] == 'function_snippet'
    sender = info['sender']
    handle = handle_lookup(sender)
    addr = handle or sender
    snippet = args['a'][0]
    snippet_digest = hashlib.sha256(snippet.encode('utf8')).hexdigest()
    put(addr, 'function', 'snippet', {
        'snippet': snippet,
        'functions': []
        }, snippet_digest)
    event('NewFunctionSnippet', [snippet_digest])
