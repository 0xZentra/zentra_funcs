import sys
import time
import json
import hashlib
import threading
import uuid
import random

import requests

import setting


CHAIN_NAME = 'base'


def proposal(height, func):
    function_sourcecode = open('../funcs/%s.py' % func, 'r').read()

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

    call = {'p': 'zentest2',
            'f': 'function_proposal',
            'a': [func, function_sourcecode, [], [], []]}
    blk['txs'].append([info, call])
    print('blk', blk)
    data = json.dumps(blk)
    requests.post('http://127.0.0.1:%s/' % setting.INDEXER_PORT, data=data.encode('utf8'))
    time.sleep(1)

def vote(height, func):
    function_sourcecode = open('../funcs/%s.py' % func, 'r').read()

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

    call = {'p': 'zentest2',
            'f': "function_vote", 
            'a': [func, hashlib.sha256(function_sourcecode.encode('utf8')).hexdigest()]}
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


    height += 1
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

    call = {'p': 'zentest2',
            'f': 'committee_init',
            'a': []}
    blk['txs'].append([info, call])
    print('blk', blk)
    data = json.dumps(blk)
    requests.post('http://127.0.0.1:%s/' % setting.INDEXER_PORT, data=data.encode('utf8'))
    time.sleep(1)


    height += 1
    proposal(height, 'function_proposal')
    height += 1
    vote(height, 'function_proposal')
    height += 1
    proposal(height, 'function_vote')
    height += 1
    vote(height, 'function_vote')
