
import hashlib
import json

import web3


PROVIDER_HOST = 'http://127.0.0.1:8545'

w3 = web3.Web3(web3.Web3.HTTPProvider(PROVIDER_HOST))


handle_purchase_sourcecode = '''
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
'''


if __name__ == '__main__':
    account = setting.account
    nonce = w3.eth.get_transaction_count(account.address)
    print(account.address, nonce)

    call = {"p": "minus",
            "f": "function_proposal",
            "a": ['handle_purchase', handle_purchase_sourcecode, [], [], []]}
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
            "a": ['handle_purchase', hashlib.sha256(handle_purchase_sourcecode.encode('utf8')).hexdigest()]}
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
