
import hashlib
import json
import getpass

import web3
import eth_account


PROVIDER_HOST = 'http://127.0.0.1:8045'

w3 = web3.Web3(web3.Web3.HTTPProvider(PROVIDER_HOST))


function_vote_sourcecode = '''
def function_vote(info, args):
    assert args['f'] == 'function_vote'
    sender = info['sender'].lower()
    handle = handle_lookup(sender)
    committee_members = set(get('committee', 'members', []))
    assert handle in committee_members

    fname = args['a'][0]
    sourcecode_hexdigest = args['a'][1]
    proposal = get('function', 'proposal', None, '%s:%s' % (fname, sourcecode_hexdigest))
    votes = set(proposal['votes'])
    votes.add(handle)
    proposal['votes'] = list(votes)

    if len(votes) >= len(committee_members)*2//3:
        put(handle, 'function', 'code', proposal, fname)
        global_state.put(('zen-code-function:%s' % (fname, )).encode('utf8'), proposal["sourcecode"].encode('utf8'))
    else:
        put(handle, 'function', 'proposal', proposal, '%s:%s' % (fname, sourcecode_hexdigest))
'''


if __name__ == '__main__':
    ps = getpass.getpass()
    js = open('account.json', 'r').read()
    sk = eth_account.Account.decrypt(json.loads(js), ps)
    account = eth_account.Account.from_key(sk)
    nonce = w3.eth.get_transaction_count(account.address)
    print(account.address, nonce)

    call = {"p": "minus",
            "f": "function_proposal",
            "a": ['function_vote', function_vote_sourcecode, [], [], []]}
    transaction = {
        'from': account.address,
        'to': account.address,
        'value': 0,
        'nonce': w3.eth.get_transaction_count(account.address),
        'data': json.dumps(call).encode('utf8'),
        'gas': 0,
        'maxFeePerGas': 0,
        'maxPriorityFeePerGas': 0,
    }

    signed = w3.eth.account.sign_transaction(transaction, account.key)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    print(tx_hash.hex())


    call = {"p": "minus",
            "f": "function_vote", 
            "a": ['function_vote', hashlib.sha256(function_vote_sourcecode.encode('utf8')).hexdigest()]}
    transaction = {
        'from': account.address,
        'to': account.address,
        'value': 0,
        'nonce': w3.eth.get_transaction_count(account.address),
        'data': json.dumps(call).encode('utf8'),
        'gas': 0,
        'maxFeePerGas': 0,
        'maxPriorityFeePerGas': 0,
    }

    signed = w3.eth.account.sign_transaction(transaction, account.key)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    print(tx_hash.hex())
