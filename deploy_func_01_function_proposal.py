
import hashlib
import json
import getpass

import web3
import eth_account


PROVIDER_HOST = 'http://127.0.0.1:8045'

w3 = web3.Web3(web3.Web3.HTTPProvider(PROVIDER_HOST))

function_proposal_sourcecode = '''
def function_proposal(info, args):
    assert args['f'] == 'function_proposal'
    sender = info['sender'].lower()
    handle = handle_lookup(sender)
    fname = args['a'][0]
    assert set(fname) <= set(string.ascii_lowercase+'_')
    sourcecode = args['a'][1]

    require = args['a'][2]
    for i in require:
        assert type(i) is list
        assert set(i[0]) <= set(string.ascii_lowercase+'_')
        assert type(i[1]) is list
        for j in i[1]:
            assert set(j) <= set(string.ascii_uppercase+'_')

    asset_permission = args['a'][3]
    assert type(asset_permission) is list
    for i in asset_permission:
        assert i == '*' or set(i) <= set(string.ascii_lowercase+'_')

    invoke_permission = args['a'][4]
    assert type(invoke_permission) is list
    for i in invoke_permission:
        assert i == '*' or set(i) <= set(string.ascii_lowercase+'_')

    hexdigest = hashlib.sha256(sourcecode.encode('utf8')).hexdigest()
    k = 'function-proposal-%s:%s' % (fname, hexdigest)
    put(handle, 'function', 'proposal', {'sourcecode': sourcecode, 'asset_permission': asset_permission, 'require': require, 'votes': []}, '%s:%s' % (fname, hexdigest))
'''


if __name__ == '__main__':
    # committee_init will only be called once and not in global state
    # function_proposal in global state
    # function_vote in global state

    ps = getpass.getpass()
    js = open('account.json', 'r').read()
    sk = eth_account.Account.decrypt(json.loads(js), ps)
    account = eth_account.Account.from_key(sk)
    nonce = w3.eth.get_transaction_count(account.address)
    print(account.address, nonce)

    # call committee_init
    call = {"p":"minus", 'f': 'committee_init', 'a': []}
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
            "f": "function_proposal",
            "a": ['function_proposal', function_proposal_sourcecode, [], [], []]}
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
            "a": ['function_proposal', hashlib.sha256(function_proposal_sourcecode.encode('utf8')).hexdigest()]}
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
