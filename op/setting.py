
import getpass
import json

import eth_account


ps = getpass.getpass()
js = json.loads(open('account.json', 'r').read())
sk = eth_account.Account.decrypt(js, ps)
account = eth_account.Account.from_key(sk)
