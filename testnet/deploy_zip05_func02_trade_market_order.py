
import hashlib
import json
import getpass
import time

import web3
import eth_account

import setting

# PROVIDER_HOST = 'http://127.0.0.1:8545'
PROVIDER_HOST = setting.rpc_url

w3 = web3.Web3(web3.Web3.HTTPProvider(PROVIDER_HOST))


trade_market_order_sourcecode = open('../funcs/trade_market_order.py', 'r').read()

if __name__ == '__main__':
    account = setting.account
    nonce = w3.eth.get_transaction_count(account.address)
    print(account.address, nonce)

    call = {'p': setting.protocol,
            'f': 'function_proposal',
            'a': ['trade_market_order', trade_market_order_sourcecode, [], [], []]}
    transaction = {
        'from': account.address,
        'to': account.address,
        'value': 0,
        'nonce': w3.eth.get_transaction_count(account.address),
        'data': json.dumps(call).encode('utf8'),
        'gas': 610000,
        'gasPrice': 1000000000,
        # 'maxFeePerGas': 3000000000,
        # 'maxPriorityFeePerGas': 0,
        'chainId': setting.chain_id
    }

    signed = w3.eth.account.sign_transaction(transaction, account.key)
    # try:
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    print(tx_hash.hex())
    # except Exception as e:
    #     pass
    time.sleep(5)


    call = {'p': setting.protocol,
            'f': "function_vote", 
            'a': ['trade_market_order', hashlib.sha256(trade_market_order_sourcecode.encode('utf8')).hexdigest()]}
    transaction = {
        'from': account.address,
        'to': account.address,
        'value': 0,
        'nonce': w3.eth.get_transaction_count(account.address),
        'data': json.dumps(call).encode('utf8'),
        'gas': 210000,
        'gasPrice': 1000000000,
        # 'maxFeePerGas': 3000000000,
        # 'maxPriorityFeePerGas': 0,
        'chainId': setting.chain_id
    }

    signed = w3.eth.account.sign_transaction(transaction, account.key)
    # try:
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    print(tx_hash.hex())
    # except Exception as e:
    #     pass
