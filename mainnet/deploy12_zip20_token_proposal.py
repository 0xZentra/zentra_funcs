
import hashlib
import json
import time

import web3
import requests

import setting

PROVIDER_HOST = setting.rpc_url

w3 = web3.Web3(web3.Web3.HTTPProvider(PROVIDER_HOST))

ZEN_ADDR = '0x00000000000000000000000000000000007A656e'# hex of 'zen'

sourcecode = open('../funcs/zip20.py', 'r').read()

if __name__ == '__main__':
    account = setting.account
    nonce = w3.eth.get_transaction_count(account.address)
    print(account.address, nonce)

    call = {'p': setting.protocol,
            'f': 'function_proposal',
            'a': [['token_create',
                   'token_mint_once',
                   'token_mint',
                   'token_burn',
                   'token_send',
                   'token_accept',
                   'token_transfer'
                   ],
                  [hashlib.sha256(sourcecode.encode('utf8')).hexdigest()]]}
    transaction = {
        'from': account.address,
        'to': ZEN_ADDR,
        'value': 0,
        'nonce': w3.eth.get_transaction_count(account.address),
        'data': json.dumps(call).encode('utf8'),
        'gas': 39240,
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
    # try:
    print(tx_hash.hex())
    # except Exception as e:
    #     pass

    tx_hash = tx_hash.hex()
    vote_no = None
    while True:
        req = requests.get(f'https://mainnet.zentra.dev/api/events?txhash={tx_hash}')
        for tx_events in req.json()['events']:
            print(tx_events)
            for event in tx_events[1]:
                if event[0] == 'function_proposal' and event[1] == 'FunctionProposal':
                    vote_no = event[2]
        print(vote_no)
        if vote_no is not None:
            break
        time.sleep(2)
