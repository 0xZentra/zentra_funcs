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

def snippet(height, func):
    sourcecode = open('../funcs/%s.py' % func, 'r').read()

    blk = {
        'txs': [],
        'block_number': height,
        'block_hash': uuid.uuid4().hex,
        'chain': CHAIN_NAME
    }
    info = {
        'sender': '0x1234'.lower(),
        'nonce': height,
        'block_number': height, 
        'block_hash': blk['block_hash'],
        'tx_index': 0,
        'tx_hash': uuid.uuid4().hex
    }

    call = {'p': setting.protocol,
            'f': 'function_snippet',
            'a': [sourcecode]}
    blk['txs'].append([info, call])
    print('blk', blk)
    data = json.dumps(blk)
    requests.post('http://127.0.0.1:%s/' % setting.INDEXER_PORT, data=data.encode('utf8'))
    time.sleep(1)

def proposal(height, func_names, snippet_hashes):
    blk = {
        'txs': [],
        'block_number': height,
        'block_hash': uuid.uuid4().hex,
        'chain': CHAIN_NAME
    }
    info = {
        'sender': '0x1234'.lower(),
        'nonce': height,
        'block_number': height, 
        'block_hash': blk['block_hash'],
        'tx_index': 0,
        'tx_hash': uuid.uuid4().hex
    }

    call = {'p': setting.protocol,
            'f': 'function_proposal',
            'a': [func_names, snippet_hashes]}
    blk['txs'].append([info, call])
    print('blk', blk)
    data = json.dumps(blk)
    requests.post('http://127.0.0.1:%s/' % setting.INDEXER_PORT, data=data.encode('utf8'))
    time.sleep(1)

def vote(height, proposal_id):
    blk = {
        'txs': [],
        'block_number': height,
        'block_hash': uuid.uuid4().hex,
        'chain': CHAIN_NAME
    }
    info = {
        'sender': '0x1234'.lower(),
        'nonce': height,
        'block_number': height, 
        'block_hash': blk['block_hash'],
        'tx_index': 0,
        'tx_hash': uuid.uuid4().hex
    }

    call = {'p': setting.protocol,
            'f': "function_vote", 
            'a': [proposal_id]}
    blk['txs'].append([info, call])
    print('blk', blk)
    data = json.dumps(blk)
    requests.post('http://127.0.0.1:%s/' % setting.INDEXER_PORT, data=data.encode('utf8'))


if __name__ == '__main__':
    from_block = 0
    req = requests.get('http://127.0.0.1:%s/height?chain=%s' % (setting.INDEXER_PORT, CHAIN_NAME))
    print(req.json())
    height = req.json()['height']
    if height is None:
        height = from_block
    print(height)

    # height += 1
    # snippet(height, 'zip2')
    height += 1
    proposal(height,
             ['function_snippet', 'function_proposal', 'function_vote'],
             ['3e4584c9f89cb04b4b9cc79182892e02c4de65883a0d70e9dee033303c445c5d'])
    height += 1
    vote(height, 2)
