import sys
import time
import json
import hashlib
import threading
import uuid
import random

import requests

import setting

from mock_zip2_function import snippet, proposal, vote

CHAIN_NAME = setting.chain


def init(height):
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
            'f': 'committee_init',
            'a': []}
    blk['txs'].append([info, call])
    print('blk', blk)
    data = json.dumps(blk)
    requests.post('http://127.0.0.1:%s/' % setting.INDEXER_PORT, data=data.encode('utf8'))
    time.sleep(1)


if __name__ == '__main__':
    from_block = 0
    req = requests.get('http://127.0.0.1:%s/height?chain=%s' % (setting.INDEXER_PORT, CHAIN_NAME))
    print(req.json())
    height = req.json()['height']
    if height is None:
        height = from_block
    print(height)

    height += 1
    init(height)
    height += 1
    snippet(height, 'zip1')
    height += 1
    proposal(height,
             ['committee_init', 'committee_add_member', 'committee_remove_member'],
             ['e5fb2b11848ff75c932891620723b60c8b1c8f3305c5307bf5a90e173d0911bd'])
    height += 1
    vote(height, 1)
