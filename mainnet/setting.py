
import hashlib
import json
import getpass

import web3
import eth_account

# account = eth_account.Account.from_key(hashlib.sha256(b'rewarder').hexdigest())

# account = eth_account.Account.from_key('0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80')

rpc_url = 'https://mainnet.base.org'
chain_id = 8453
chain = 'base'
protocol = 'zentest'

ps = getpass.getpass()
js = open('../account.json', 'r').read()
sk = eth_account.Account.decrypt(json.loads(js), ps)
account = eth_account.Account.from_key(sk)
