
import hashlib
import json
import sys
import time
import urllib.request

import web3
import eth_account

API_BASE = 'https://testnet3.zentra.dev'

ZEN_ADDR = '0x00000000000000000000000000000000007A656e'# hex of 'zen'

sourcecode = open('../funcs/zip24.py', 'r').read()
snippet_digest = hashlib.sha256(sourcecode.encode('utf8')).hexdigest()


def snippet_deployed(digest):
    prefix = 'base-function-snippet:' + digest
    url = '%s/api/get_latest_state?prefix=%s' % (API_BASE, prefix)
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (compatible; zentra-script)'},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf8'))
    except Exception as e:
        print('Warning: deploy check failed, continuing. API error:', e)
        return False
    return data.get('result') is not None


if __name__ == '__main__':
    if snippet_deployed(snippet_digest):
        print('Snippet already deployed: %s' % snippet_digest)
        sys.exit(0)

    import setting

    # PROVIDER_HOST = 'http://127.0.0.1:8545'
    PROVIDER_HOST = setting.rpc_url

    w3 = web3.Web3(web3.Web3.HTTPProvider(PROVIDER_HOST))

    account = setting.account
    nonce = w3.eth.get_transaction_count(account.address)
    print(account.address, nonce)

    call = {'p': setting.protocol,
            'f': 'function_snippet',
            'a': [sourcecode]}
    data = json.dumps(call).encode('utf8')
    transaction = {
        'from': account.address,
        'to': ZEN_ADDR,
        'value': 0,
        'nonce': w3.eth.get_transaction_count(account.address),
        'data': data,
        'gas': 21000 + len(data) * 48,
        'gasPrice': 1000000000,
        # 'maxFeePerGas': 3000000000,
        # 'maxPriorityFeePerGas': 0,
        'chainId': setting.chain_id
    }

    signed = w3.eth.account.sign_transaction(transaction, account.key)
    # try:
    # try:
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    # except:
    #     tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    print(tx_hash.hex())
    # except Exception as e:
    #     pass

    time.sleep(5)
