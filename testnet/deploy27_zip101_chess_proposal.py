
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

ZEN_ADDR = '0x00000000000000000000000000000000007A656e'# hex of 'zen'

sourcecode = open('../funcs/zip101.py', 'r').read()

if __name__ == '__main__':
    account = setting.account
    nonce = w3.eth.get_transaction_count(account.address)
    print(account.address, nonce)

    call = {'p': setting.protocol,
            'f': 'function_proposal',
            'a': [['chess_init',
                   'chess_create_game',
                   'chess_join_game',
                   'chess_cancel_game',
                   'chess_make_move',
                   'chess_predict_limit_order',
                   'chess_predict_market_order',
                   'chess_predict_limit_order_cancel',
                   'chess_predict_create',
                   'chess_predict_mint',
                   'chess_set_quote_tokens',
                   'chess_update_manager'
                   ],
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
    # try:
    try:
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    except:
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    print(tx_hash.hex())
    # except Exception as e:
    #     pass

