
import hashlib
import json

import web3


PROVIDER_HOST = 'http://127.0.0.1:8545'

w3 = web3.Web3(web3.Web3.HTTPProvider(PROVIDER_HOST))


handle_pow_sourcecode = '''
def handle_pow(info, args):
    assert args['f'] == 'handle_pow'
    # height = args['a'][0]
    header = args['a'][0]
    handle = args['a'][1]
    nonce = args['a'][2]
    h = header[8:8+64]
    blockhash = h[6:8]+h[4:6]+h[2:4]+h[0:2] \
            + h[14:16]+h[12:14]+h[10:12]+h[8:10] \
            + h[22:24]+h[20:22]+h[18:20]+h[16:18] \
            + h[30:32]+h[28:30]+h[26:28]+h[24:26] \
            + h[38:40]+h[36:38]+h[34:36]+h[32:34] \
            + h[46:48]+h[44:46]+h[42:44]+h[40:42] \
            + h[54:56]+h[52:54]+h[50:52]+h[48:50] \
            + h[62:64]+h[60:62]+h[58:60]+h[56:58]
    t = header[8+64+64:8+64+64+8]
    timestamp = int(t[6:8]+t[4:6]+t[2:4]+t[0:2], 16)
    print('timestamp', timestamp)
    asset = 'handle'
    sender = info['sender'].lower()

    recent = get(asset, 'recent', [])
    recent_change = False
    if blockhash not in recent:
        recent.append(blockhash)
        recent_change = True
    if len(recent) > 1:
        blockhash_to_reward = recent.pop(0)
        recent_change = True

        block_reward = get(asset, 'block', {}, blockhash_to_reward)
        for handle_reward, (header_reward, nonce_reward) in block_reward.items():
            header_reward, nonce_reward = block_reward[handle_reward]
            c1 = hashlib.sha256(bytes.fromhex(header_reward) + nonce_reward.to_bytes(4, byteorder='little')).digest()
            c2 = hashlib.sha256(c1).digest()
            c_int = int.from_bytes(bytes.fromhex(c2.hex()), 'little')
            total = get(asset, 'total', 0, handle_reward)
            credit = 2**256 * 10**18 // (c_int * timestamp)
            bonus = int(credit ** 1.1)
            total = int(total + bonus)
            # print('bonus', bonus)
            put(sender, asset, 'total', total, handle_reward)
            put(sender, asset, 'credit', credit, handle_reward)
            put(sender, asset, 'bonus', bonus, handle_reward)

    if recent_change:
        put(sender, asset, 'recent', recent)

    block = get(asset, 'block', {}, blockhash)
    if block.get(handle):
        prev_header, prev_nonce = block[handle]
        p1 = hashlib.sha256(bytes.fromhex(prev_header) + prev_nonce.to_bytes(4, byteorder='little')).digest()
        p2 = hashlib.sha256(p1).digest()
        p_int = int.from_bytes(bytes.fromhex(p2.hex()), 'little')
    else:
        p_int = 2**256

    h1 = hashlib.sha256(bytes.fromhex(header) + nonce.to_bytes(4, byteorder='little')).digest()
    h2 = hashlib.sha256(h1).digest()
    h_int = int.from_bytes(bytes.fromhex(h2.hex()), 'little')
    if h_int < p_int:
        block[handle] = [header, nonce]
        put(sender, asset, 'block', block, blockhash)
'''


if __name__ == '__main__':
    account = setting.account
    nonce = w3.eth.get_transaction_count(account.address)
    print(account.address, nonce)

    call = {"p": "minus",
            "f": "function_proposal",
            "a": ['handle_pow', handle_pow_sourcecode, [], [], []]}
    transaction = {
        'from': account.address,
        'to': account.address,
        'value': 0,
        'nonce': w3.eth.get_transaction_count(account.address),
        'data': json.dumps(call).encode('utf8'),
        'gas': 0,
        'maxFeePerGas': 0,
        'maxPriorityFeePerGas': 0,
    }

    signed = w3.eth.account.sign_transaction(transaction, account.key)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    print(tx_hash.hex())


    call = {"p": "minus",
            "f": "function_vote", 
            "a": ['handle_pow', hashlib.sha256(handle_pow_sourcecode.encode('utf8')).hexdigest()]}
    transaction = {
        'from': account.address,
        'to': account.address,
        'value': 0,
        'nonce': w3.eth.get_transaction_count(account.address),
        'data': json.dumps(call).encode('utf8'),
        'gas': 0,
        'maxFeePerGas': 0,
        'maxPriorityFeePerGas': 0,
    }

    signed = w3.eth.account.sign_transaction(transaction, account.key)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    print(tx_hash.hex())
