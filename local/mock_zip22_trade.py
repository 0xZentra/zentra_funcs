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

if __name__ == '__main__':
    from_block = 0
    req = requests.get('http://127.0.0.1:%s/height?chain=%s' % (setting.INDEXER_PORT, CHAIN_NAME))
    print(req.json())
    height = req.json()['height']
    if height is None:
        height = from_block
    print(height)

    height += 1
    sourcecode_hash = snippet(height, 'zip22')

    height += 1
    proposal(height,
            ['trade_limit_order', 'trade_market_order', 'trade_limit_order_cancel', 'trade_pair_create', 'trade_set_quote_token'],
            [sourcecode_hash])
    height += 1
    vote(height, 6)
