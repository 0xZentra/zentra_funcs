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


CHAIN_NAME = 'base'


if __name__ == '__main__':
    from_block = 0
    req = requests.get('http://127.0.0.1:%s/height?chain=%s' % (setting.INDEXER_PORT, CHAIN_NAME))
    print(req.json())
    height = req.json()['height']
    if height is None:
        height = from_block
    print(height)

    height += 1
    snippet(height, 'zip20')
    height += 1
    proposal(height,
            ['token_create', 'token_mint_once', 'token_mint', 'token_burn', 'token_transfer'],
            ['2f364fa5ebb7de5ea49c6d5b882b4a0928ca90d3658e383d25350d69ab777a8a'])
    height += 1
    vote(height, 4)
    height += 1
