import sys
import time
import json
import hashlib
import threading
import uuid
import random

import requests

import setting



CHAIN_NAME = setting.chain

from_block = 0

req = requests.get('http://127.0.0.1:%s/height?chain=%s' % (setting.INDEXER_PORT, CHAIN_NAME))
print(req.json())
height = req.json()['height']
if height is None:
    height = from_block
print(height)

blk = {
    'txs': [],
    'block_number': height+1,
    'block_hash': uuid.uuid4().hex,
    'chain': CHAIN_NAME
}

addr = sys.argv[1]
nonce = height + 1

for i, calldata in enumerate(sys.argv[2:]):
    info = {
        'sender': addr.lower(),
        'nonce': nonce + i,
        'block_number': height+1,
        'block_hash': blk['block_hash'],
        'tx_index': i,
        'tx_hash': uuid.uuid4().hex
    }

    # call = {'p': 'zentest',
    #         'f': 'transfer',
    #         'a': [a3, a2, a4]}
    calldata = calldata.strip('"')# '{"p": "zentest", "f": "handle_purchase", "a": ["powid5"]}'
    call = json.loads(calldata)

    blk['txs'].append([info, call])
print('blk', blk)
data = json.dumps(blk)
requests.post('http://127.0.0.1:%s/' % setting.INDEXER_PORT, data=data.encode('utf8'))
time.sleep(1)
