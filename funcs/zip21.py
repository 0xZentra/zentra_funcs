
# Elliptic Curve parameters for secp256k1
# P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
# A = 0
# B = 7
# Gx = 55066263022277343669578718895168534326250603453777594175500187360389116729240
# Gy = 32670510020758816978083085130507043184471273380659243275938904335757337482424
# G = (Gx, Gy)
# N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
# K = 10**18

# def _inverse_mod(k, p):
#     if k == 0:
#         raise
#     return pow(k, p - 2, p)

# def _is_on_curve(point):
#     if point is None:
#         return True
#     x, y = point
#     return (y * y - (x * x * x + A * x + B)) % P == 0

# def _point_add(point1, point2):
#     if point1 is None:
#         return point2
#     if point2 is None:
#         return point1
#     x1, y1 = point1
#     x2, y2 = point2
#     if x1 == x2 and y1 != y2:
#         return None
#     if x1 == x2:
#         m = (3 * x1 * x1 + A) * _inverse_mod(2 * y1, P)
#     else:
#         m = (y2 - y1) * _inverse_mod(x2 - x1, P)
#     m %= P
#     x3 = (m * m - x1 - x2) % P
#     y3 = (m * (x1 - x3) - y1) % P
#     return (x3, y3)

# def _scalar_mult(k, point):
#     result = None
#     addend = point
#     while k:
#         if k & 1:
#             result = _point_add(result, addend)
#         addend = _point_add(addend, addend)
#         k >>= 1
#     return result

# def _ecdsa_verify(msg_hash_hex, signature_hex, public_key_hex):
#     assert msg_hash_hex.startswith('0x')
#     assert signature_hex.startswith('0x')
#     assert public_key_hex.startswith('0x')
#     r = int(signature_hex[2:66], 16)
#     s = int(signature_hex[66:130], 16)
#     if not (1 <= r < N and 1 <= s < N):
#         return False
#     point = (int(public_key_hex[2:66], 16), int(public_key_hex[66:], 16))
#     # print(type(msg_hash_hex), msg_hash_hex)
#     e = int(msg_hash_hex[2:], 16)
#     w = _inverse_mod(s, N)
#     u1 = (e * w) % N
#     u2 = (r * w) % N
#     q = _point_add(_scalar_mult(u1, G), _scalar_mult(u2, point))
#     if q is None:
#         return False
#     x, y = q
#     return r == x % N

# def _ecdsa_recover(msg_hash_hex, signature_hex):
#     assert msg_hash_hex.startswith('0x')
#     assert signature_hex.startswith('0x')
#     r = int(signature_hex[2:66], 16)
#     s = int(signature_hex[66:130], 16)
#     z = int(msg_hash_hex[2:], 16)

#     if len(signature_hex[2:]) == 130:
#         v = int(signature_hex[130:], 16)
#         if v >= 27:
#             recovery_id = v - 27
#         else:
#             recovery_id = v
#         recovery_ids = [recovery_id]
#     else:
#         recovery_ids = [0, 1]

#     for recovery_id in recovery_ids:
#         for j in range(2):
#             x = r + j * N
#             if x >= P:
#                 continue

#             y_squared = (pow(x, 3, P) + A * x + B) % P
#             y = pow(y_squared, (P + 1) // 4, P)

#             if y % 2 != recovery_id:
#                 y = P - y

#             point = (x, y)
#             if not _is_on_curve(point):
#                 continue

#             r_inv = _inverse_mod(r, N)
#             u1 = (-z * r_inv) % N
#             u2 = (s * r_inv) % N

#             q = _point_add(_scalar_mult(u1, G), _scalar_mult(u2, point))
#             if q is None:
#                 continue

#             public_key_hex = f"0x{q[0]:064x}{q[1]:064x}"
#             if _ecdsa_verify(msg_hash_hex, signature_hex, public_key_hex):
#                 return public_key_hex

#     return None


# def _encode_uint256(value):
#     return value.to_bytes(32, 'big')

# def _encode_address(address_str):
#     address_bytes = bytes.fromhex(address_str[2:])
#     return b'\x00' * (32 - len(address_bytes)) + address_bytes

# def _encode_dynamic_bytes(data_hex):
#     data_bytes = bytes.fromhex(data_hex)
#     length = len(data_bytes)
#     padded_length = (length + 31) // 32 * 32 # Calculate padded length for data
#     return length.to_bytes(32, 'big') + data_bytes + b'\x00' * (padded_length - length)

# # '{"a": [845300000000000000000000002, 8453, 43114, "0x51055892893c17ae7db48a0c0f760145bfe9f1e5", "0x09ace2d19b0273a762b0fe22b9e5199505c778de", 0, "000000000000000000000000490537058bdddaae99dd4da8b5db5675936bfedf0000000000000000000000000000000000000000000000008ac7230489e80000", "0000000000000000000000000000000000000000000000000000000000000000", "034da1308a53b6586fed90af2bd4e48cc863913551cc41d6148f43441691e4fd1ea27a1e3daf2b4c1386d0426cc37a4423729204177740768970937c93d648961c"], "f": "bridge_incoming_process", "p": "zentest"}'
# def bridge_incoming_process(info, args):
#     assert args['f'] == 'bridge_incoming_process'
#     sender = info['sender']
#     addr = handle_lookup(sender)
#     print('bridge_incoming_process')

#     txid = args['a'][0]
#     source_chain_id = args['a'][1]
#     dest_chain_id = args['a'][2]
#     source_chain_sender = args['a'][3]
#     dest_chain_recipient = args['a'][4]
#     gas = args['a'][5]
#     user_payload = args['a'][6]
#     exsig = args['a'][7]
#     signature = args['a'][8]

#     encoded_txid = _encode_uint256(txid)
#     encoded_source_chain_id = _encode_uint256(source_chain_id)
#     encoded_dest_chain_id = _encode_uint256(dest_chain_id)
#     encoded_source_chain_sender = _encode_address(source_chain_sender)
#     encoded_dest_chain_recipient = _encode_address(dest_chain_recipient)
#     offset_user_payload = 6 * 32
#     encoded_offset_user_payload = _encode_uint256(offset_user_payload)

#     header = b''.join([
#         encoded_txid,
#         encoded_source_chain_id,
#         encoded_dest_chain_id,
#         encoded_source_chain_sender,
#         encoded_dest_chain_recipient,
#         encoded_offset_user_payload,
#     ])
#     encoded_user_payload_data = _encode_dynamic_bytes(user_payload)

#     encoded_data = b''.join([
#         header,
#         encoded_user_payload_data,
#     ])
#     print(f"ABI Encoded Data (Pure Python): 0x{encoded_data.hex()}")

#     encoded_data_hash = keccak(encoded_data)
#     x19_msg_prefix = b"\x19Ethereum Signed Message:\n" + str(len(encoded_data_hash)).encode('utf-8')
#     x19_msg_hash = keccak(x19_msg_prefix + encoded_data_hash)
#     print(f"x19_msg (Pure Python): 0x{x19_msg_hash.hex()}")

#     print('x19', '0x'+x19_msg_hash.hex())
#     print('signature', '0x'+signature)
#     recovered_public_key = _ecdsa_recover('0x'+x19_msg_hash.hex(), '0x'+signature)
#     print(f"recovered public key: {recovered_public_key}")
#     if recovered_public_key:
#         public_key_bytes = bytes.fromhex(recovered_public_key[2:])
#         address_bytes = keccak(public_key_bytes)[-20:]
#         address = '0x' + address_bytes.hex()
#         print(f"Recovered Ethereum address: {address}")


# def bridge_incoming(info, args):
#     assert args['f'] == 'bridge_incoming'
#     print('bridge_incoming', args)

#     tick = args['a'][0]
#     assert type(tick) is str
#     assert len(tick) > 0 and len(tick) < 42
#     assert tick[0] in string.ascii_uppercase
#     assert set(tick) <= set(string.ascii_uppercase+string.digits+'_')

#     operator, _ = get(tick, 'incoming_operator', None)
#     assert operator is not None, "Bridge is not initialized"
#     sender = info['sender']
#     assert sender == operator, "Only the operator can perform this operation"

#     amount = int(args['a'][1])
#     assert amount > 0

#     receiver = args['a'][2].lower()
#     assert len(receiver) <= 42
#     assert type(receiver) is str
#     if len(receiver) == 42:
#         assert receiver.startswith('0x')
#         assert set(receiver[2:]) <= set(string.digits+'abcdef')
#     else:
#         assert len(receiver) > 4

#     balance, _ = get(tick, 'balance', 0, receiver)
#     balance = int(balance)
#     balance += amount
#     put(receiver, tick, 'balance', balance, receiver)

#     asset_owner, _ = get('asset', 'owner', None, tick)
#     total, _ = get(tick, 'total', 0)
#     total = int(total)
#     total += amount
#     put(asset_owner, tick, 'total', total)

#     # call('trade_market_order', ['USDC', None, 'ZENT', 50 * 10**18 // 1000])
#     # sender_balance, _ = get(tick_1, 'balance', 0, addr)
#     print('tick', tick, 'balance', balance)
#     # print('quote_value > 0', quote_value)

#     if tick != 'USDC':
#         return

#     base_tick = 'ZENT'
#     quote_tick = tick
#     pair = '%s_%s' % (base_tick, quote_tick)
#     addr = receiver
#     quote_sum = 0
#     quote_balance = balance
#     base_value = 10**18 // 1000 * 50 # 50 bytes
#     trade_sell_start, _ = get('trade', f'{pair}_sell_start', 1)
#     # trade_buy_start, _ = get('trade', f'{pair}_buy_start', 1)

#     # break until the base balance is enough
#     trade_sell_id = trade_sell_start
#     while True:
#         sell, _ = get('trade', f'{pair}_sell', None, str(trade_sell_id))
#         if sell is None:
#             break

#         price = sell[3]
#         print(-sell[1], quote_balance * K // price, base_value)
#         dx_base = min(-sell[1], quote_balance * K // price, base_value)
#         dx_quote = dx_base * price // K
#         if dx_base == 0 or dx_quote == 0:
#             break
#         sell[1] += dx_base
#         sell[2] -= dx_quote

#         if quote_balance - dx_quote < 0:
#             break
#         quote_balance -= dx_quote
#         quote_sum += dx_quote

#         if sell[1] == 0 or sell[1] // price == 0:
#             if sell[4]:
#                 prev_sell, _ = get('trade', f'{pair}_sell', None, str(sell[4]))
#                 prev_sell[5] = sell[5]
#                 put(prev_sell[0], 'trade', f'{pair}_sell', prev_sell, str(sell[4]))

#             if sell[5]:
#                 next_sell, _ = get('trade', f'{pair}_sell', None, str(sell[5]))
#                 next_sell[4] = sell[4]
#                 put(next_sell[0], 'trade', f'{pair}_sell', next_sell, str(sell[5]))

#             if sell[4] is not None and sell[5] is None:
#                 trade_sell_start = sell[4]
#                 put(addr, 'trade', f'{pair}_sell_start', trade_sell_start)
#             elif sell[4] is None and sell[5] is None:
#                 trade_sell_new, _ = get('trade', f'{pair}_sell_new', 1)
#                 trade_sell_start = trade_sell_new
#                 put(addr, 'trade', f'{pair}_sell_start', trade_sell_start)

#             print(f'{pair}_sell_to_refund', sell)
#             if sell[1] < 0:
#                 balance, _ = get(base_tick, 'balance', 0, sell[0])
#                 balance -= sell[1]
#                 assert balance >= 0
#                 put(sell[0], base_tick, 'balance', balance, sell[0])

#             put(sell[0], 'trade', f'{pair}_sell', None, str(trade_sell_id))
#         else:
#             put(sell[0], 'trade', f'{pair}_sell', sell, str(trade_sell_id))

#         balance, _ = get(quote_tick, 'balance', 0, sell[0])
#         balance += dx_quote
#         assert balance >= 0
#         put(addr, quote_tick, 'balance', balance, sell[0])

#         base_value -= dx_base
#         assert base_value >= 0
#         balance, _ = get(base_tick, 'balance', 0, addr)
#         balance += dx_base
#         assert balance >= 0
#         put(addr, base_tick, 'balance', balance, addr)

#         if sell[4] is None:
#             break
#         trade_sell_id = sell[4]

#     balance, _ = get(quote_tick, 'balance', 0, addr)
#     balance -= quote_sum
#     assert balance >= 0
#     put(addr, quote_tick, 'balance', balance, addr)


def bridge_incoming(info, args):
    assert args['f'] == 'bridge_incoming'
    print('bridge_incoming', args)

    tick = args['a'][0]
    assert type(tick) is str
    assert len(tick) > 0 and len(tick) < 42
    assert tick[0] in string.ascii_uppercase
    assert set(tick) <= set(string.ascii_uppercase+string.digits+'_')

    operator, _ = get(tick, 'incoming_operator', None)
    assert operator is not None, "Bridge is not initialized"
    sender = info['sender']
    assert sender == operator, "Only the operator can perform this operation"

    amount = int(args['a'][1])
    assert amount > 0

    receiver = args['a'][2].lower()
    assert len(receiver) <= 42
    assert type(receiver) is str
    if len(receiver) == 42:
        assert receiver.startswith('0x')
        assert set(receiver[2:]) <= set(string.digits+'abcdef')
    else:
        assert len(receiver) > 4

    balance, _ = get(tick, 'balance', 0, receiver)
    balance = int(balance)
    balance += amount
    put(receiver, tick, 'balance', balance, receiver)

    asset_owner, _ = get('asset', 'owner', None, tick)
    total, _ = get(tick, 'total', 0)
    total = int(total)
    total += amount
    put(asset_owner, tick, 'total', total)


def bridge_outgoing(info, args):
    assert args['f'] == 'bridge_outgoing'

    tick = args['a'][0]
    assert type(tick) is str
    assert len(tick) > 0 and len(tick) < 42
    assert tick[0] in string.ascii_uppercase
    assert set(tick) <= set(string.ascii_uppercase+string.digits+'_')

    amount = int(args['a'][1])
    assert amount > 0

    chain = args['a'][2]
    assert chain in ['op-sepolia']

    sender = info['sender']


def bridge_set_operator(info, args):
    assert args['f'] == 'bridge_set_operator'
    print('bridge_set_operator', args)

    tick = args['a'][0]
    assert type(tick) is str
    assert len(tick) > 0 and len(tick) < 42
    assert tick[0] in string.ascii_uppercase
    assert set(tick) <= set(string.ascii_uppercase+string.digits+'_')

    asset_owner, _ = get('asset', 'owner', None, tick)
    sender = info['sender']
    addr = handle_lookup(sender)
    print('bridge_set_operator', asset_owner, addr)
    assert addr == asset_owner, "Only the asset owner can perform this operation"

    operator = args['a'][1].lower()
    assert type(operator) is str
    # assert len(operator) == 42
    assert operator.startswith('0x')
    assert set(operator[2:]) <= set(string.digits+'abcdef')

    put(addr, tick, 'incoming_operator', operator)


def bridge_remove_operator(info, args):
    assert args['f'] == 'bridge_remove_operator'
    print('bridge_remove_operator', args)

    tick = args['a'][0]
    assert type(tick) is str
    assert len(tick) > 0 and len(tick) < 42
    assert tick[0] in string.ascii_uppercase
    assert set(tick) <= set(string.ascii_uppercase+string.digits+'_')

    asset_owner, _ = get('asset', 'owner', None, tick)
    sender = info['sender']
    addr = handle_lookup(sender)
    # print('bridge_remove_operator', asset_owner, addr)
    assert addr == asset_owner, "Only the asset owner can perform this operation"

    # operator = args['a'][1].lower()
    # assert type(operator) is str
    # assert len(operator) == 42
    # assert operator.startswith('0x')
    # assert set(operator[2:]) <= set(string.digits+'abcdef')

    put(addr, tick, 'incoming_operator', None)

def bridge_set_outgoing_fee(info, args):
    assert args['f'] == 'bridge_set_outgoing_fee'
    print('bridge_set_outgoing_fee', args)
