
import json
import getpass

import eth_account

# rpc_url = 'http://127.0.0.1:8545'
rpc_url = 'https://sepolia.base.org'
chain_id = 84532
chain = 'base'
protocol = 'zentest3'

# account = eth_account.Account.from_key('0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80')

ps = getpass.getpass()
js = open('../account.json', 'r').read()
sk = eth_account.Account.decrypt(json.loads(js), ps)
account = eth_account.Account.from_key(sk)
