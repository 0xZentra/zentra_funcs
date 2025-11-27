
import json
import getpass
# import hashlib

# import web3
import eth_account


rpc_url = 'https://mainnet.base.org'
chain_id = 8453
chain = 'base'
protocol = 'zen'


ps = getpass.getpass()
js = open('../account.json', 'r').read()
sk = eth_account.Account.decrypt(json.loads(js), ps)
account = eth_account.Account.from_key(sk)
