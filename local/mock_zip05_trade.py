import sys
import time
import json
import hashlib
import threading
import uuid
import random

import requests

import setting

from mock_zip01_function import proposal, vote


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
    proposal(height, 'trade_limit_order')
    height += 1
    vote(height, 'trade_limit_order')

    height += 1
    proposal(height, 'trade_market_order')
    height += 1
    vote(height, 'trade_market_order')

    height += 1
    proposal(height, 'trade_order_cancel')
    height += 1
    vote(height, 'trade_order_cancel')

    height += 1
    proposal(height, 'trade_pair_create')
    height += 1
    vote(height, 'trade_pair_create')

    height += 1
    proposal(height, 'trade_set_quote_token')
    height += 1
    vote(height, 'trade_set_quote_token')
