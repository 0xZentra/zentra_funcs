
import hashlib
import json
import getpass
import time

import requests
import web3
import eth_account

import setting

# PROVIDER_HOST = 'http://127.0.0.1:8545'
PROVIDER_HOST = setting.rpc_url

w3 = web3.Web3(web3.Web3.HTTPProvider(PROVIDER_HOST))

ZEN_ADDR = '0x00000000000000000000000000000000007A656e'# hex of 'zen'

sourcecode = open('../funcs/zip21.py', 'r').read()

if __name__ == '__main__':
    account = setting.account

    nonce = w3.eth.get_transaction_count(account.address)
    print(account.address, nonce)

    call = {'p': setting.protocol,
            'f': 'function_snippet',
            'a': [sourcecode]}
    transaction = {
        'from': account.address,
        'to': ZEN_ADDR,
        'value': 0,
        'nonce': w3.eth.get_transaction_count(account.address),
        'data': json.dumps(call).encode('utf8'),
        'gas': 670000,
        'gasPrice': 1000000000,
        # 'maxFeePerGas': 3000000000,
        # 'maxPriorityFeePerGas': 0,
        'chainId': setting.chain_id
    }

    signed = w3.eth.account.sign_transaction(transaction, account.key)
    try:
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    except:
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    print(tx_hash.hex())
    time.sleep(5)


    nonce = w3.eth.get_transaction_count(account.address)
    print(account.address, nonce)

    call = {'p': setting.protocol,
            'f': 'function_proposal',
            'a': [['bridge_incoming_process', 'bridge_incoming', 'bridge_outgoing', 'bridge_set_operator', 'bridge_unset_operator', 'bridge_set_outgoing_fee'],
                  [hashlib.sha256(sourcecode.encode('utf8')).hexdigest()]]}
    transaction = {
        'from': account.address,
        'to': ZEN_ADDR,
        'value': 0,
        'nonce': w3.eth.get_transaction_count(account.address),
        'data': json.dumps(call).encode('utf8'),
        'gas': 40000,
        'gasPrice': 1000000000,
        # 'maxFeePerGas': 3000000000,
        # 'maxPriorityFeePerGas': 0,
        'chainId': setting.chain_id
    }

    signed = w3.eth.account.sign_transaction(transaction, account.key)
    try:
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    except:
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    print(tx_hash.hex())
    time.sleep(5)

    tx_hash = tx_hash.hex()
    # tx_hash = 'f95e0e74b4a4abf56c680c8dbbcdd2b80780ee62a171b04bf7189f764981a7d3'
    nonce = w3.eth.get_transaction_count(account.address)
    print(account.address, nonce)
    vote_no = None
    while True:
        req = requests.get(f'https://testnet3.zentra.dev/api/events?txhash={tx_hash}')
        for tx_events in req.json()['events']:
            print(tx_events)
            for event in tx_events[1]:
                if event[0] == 'function_proposal' and event[1] == 'FunctionProposal':
                    vote_no = event[2]
        print(vote_no)
        if vote_no is not None:
            break
        time.sleep(2)

    call = {'p': setting.protocol,
            'f': "function_vote", 
            'a': [vote_no]}
    transaction = {
        'from': account.address,
        'to': ZEN_ADDR,
        'value': 0,
        'nonce': w3.eth.get_transaction_count(account.address),
        'data': json.dumps(call).encode('utf8'),
        'gas': 25960,
        'gasPrice': 1000000000,
        # 'maxFeePerGas': 3000000000,
        # 'maxPriorityFeePerGas': 0,
        'chainId': setting.chain_id
    }

    signed = w3.eth.account.sign_transaction(transaction, account.key)
    try:
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    except:
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    print(tx_hash.hex())


