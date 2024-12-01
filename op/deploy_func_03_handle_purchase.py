
import hashlib
import json
import getpass
import time

import web3
import web3.gas_strategies.time_based
import eth_account

import setting

# PROVIDER_HOST = 'http://127.0.0.1:8545'
PROVIDER_HOST = 'https://mainnet.optimism.io'
CHAIN_ID = 10

w3 = web3.Web3(web3.Web3.HTTPProvider(PROVIDER_HOST))
w3.eth.set_gas_price_strategy(web3.gas_strategies.time_based.medium_gas_price_strategy)
gas_price = w3.eth.generate_gas_price()


handle_purchase_sourcecode = open('../funcs/handle_purchase.py', 'r').read()


if __name__ == '__main__':
    account = setting.account
    nonce = w3.eth.get_transaction_count(account.address)
    print(account.address, nonce)

    call = {'p': 'zen',
            'f': 'function_proposal',
            'a': ['handle_purchase', handle_purchase_sourcecode, [], [], []]}
    transaction = {
        'from': account.address,
        'to': account.address,
        'value': 0,
        'nonce': w3.eth.get_transaction_count(account.address),
        'data': json.dumps(call).encode('utf8'),
        'gas': 210000,
        'gasPrice': gas_price,
        # 'maxFeePerGas': 3000000000,
        # 'maxPriorityFeePerGas': 0,
        'chainId': CHAIN_ID
    }

    signed = w3.eth.account.sign_transaction(transaction, account.key)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    print(tx_hash.hex())
    time.sleep(5)


    call = {'p': 'zen',
            'f': "function_vote", 
            'a': ['handle_purchase', hashlib.sha256(handle_purchase_sourcecode.encode('utf8')).hexdigest()]}
    transaction = {
        'from': account.address,
        'to': account.address,
        'value': 0,
        'nonce': w3.eth.get_transaction_count(account.address),
        'data': json.dumps(call).encode('utf8'),
        'gas': 210000,
        'gasPrice': gas_price,
        # 'maxFeePerGas': 3000000000,
        # 'maxPriorityFeePerGas': 0,
        'chainId': CHAIN_ID
    }

    signed = w3.eth.account.sign_transaction(transaction, account.key)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    print(tx_hash.hex())
