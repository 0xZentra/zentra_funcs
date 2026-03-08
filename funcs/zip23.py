# Paillier helpers + privacy transfer flow (ZIP23)

def _egcd(a, b):
    x0, y0 = 1, 0
    x1, y1 = 0, 1
    while b != 0:
        q = a // b
        a, b = b, a % b
        x0, x1 = x1, x0 - q * x1
        y0, y1 = y1, y0 - q * y1
    return a, x0, y0

def _modinv(a, n):
    g, x, _ = _egcd(a, n)
    assert g == 1
    return x % n

def _homomorphic_add(pub, c1, c2):
    n = pub
    n2 = n * n
    return (c1 * c2) % n2

def _homomorphic_sub(pub, c1, c2):
    n = pub
    n2 = n * n
    inv = _modinv(c2, n2)
    return (c1 * inv) % n2


# Elliptic Curve parameters for secp256k1
P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
A = 0
B = 7
Gx = 55066263022277343669578718895168534326250603453777594175500187360389116729240
Gy = 32670510020758816978083085130507043184471273380659243275938904335757337482424
G = (Gx, Gy)
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

def _inverse_mod(k, p):
    if k == 0:
        raise
    return pow(k, p - 2, p)

def _is_on_curve(point):
    if point is None:
        return True
    x, y = point
    return (y * y - (x * x * x + A * x + B)) % P == 0

def _point_add(point1, point2):
    if point1 is None:
        return point2
    if point2 is None:
        return point1
    x1, y1 = point1
    x2, y2 = point2
    if x1 == x2 and y1 != y2:
        return None
    if x1 == x2:
        m = (3 * x1 * x1 + A) * _inverse_mod(2 * y1, P)
    else:
        m = (y2 - y1) * _inverse_mod(x2 - x1, P)
    m %= P
    x3 = (m * m - x1 - x2) % P
    y3 = (m * (x1 - x3) - y1) % P
    return (x3, y3)

def _scalar_mult(k, point):
    result = None
    addend = point
    while k:
        if k & 1:
            result = _point_add(result, addend)
        addend = _point_add(addend, addend)
        k >>= 1
    return result

def _ecdsa_verify(msg_hash_hex, signature_hex, public_key_hex):
    assert msg_hash_hex.startswith('0x')
    assert signature_hex.startswith('0x')
    assert public_key_hex.startswith('0x')
    r = int(signature_hex[2:66], 16)
    s = int(signature_hex[66:130], 16)
    if not (1 <= r < N and 1 <= s < N):
        return False
    point = (int(public_key_hex[2:66], 16), int(public_key_hex[66:], 16))
    e = int(msg_hash_hex[2:], 16)
    w = _inverse_mod(s, N)
    u1 = (e * w) % N
    u2 = (r * w) % N
    q = _point_add(_scalar_mult(u1, G), _scalar_mult(u2, point))
    if q is None:
        return False
    x, y = q
    return r == x % N

def _ecdsa_recover(msg_hash_hex, signature_hex):
    assert msg_hash_hex.startswith('0x')
    assert signature_hex.startswith('0x')
    r = int(signature_hex[2:66], 16)
    s = int(signature_hex[66:130], 16)
    z = int(msg_hash_hex[2:], 16)

    if len(signature_hex[2:]) == 130:
        v = int(signature_hex[130:], 16)
        if v >= 27:
            recovery_id = v - 27
        else:
            recovery_id = v
        recovery_ids = [recovery_id]
    else:
        recovery_ids = [0, 1]

    for recovery_id in recovery_ids:
        for j in range(2):
            x = r + j * N
            if x >= P:
                continue

            y_squared = (pow(x, 3, P) + A * x + B) % P
            y = pow(y_squared, (P + 1) // 4, P)

            if y % 2 != recovery_id:
                y = P - y

            point = (x, y)
            if not _is_on_curve(point):
                continue

            r_inv = _inverse_mod(r, N)
            u1 = (-z * r_inv) % N
            u2 = (s * r_inv) % N

            q = _point_add(_scalar_mult(u1, G), _scalar_mult(u2, point))

            if q is None:
                continue

            public_key_hex = f"0x{q[0]:064x}{q[1]:064x}"
            if _ecdsa_verify(msg_hash_hex, signature_hex, public_key_hex):
                return public_key_hex

    return None

def _pubkey_to_address(public_key_hex):
    public_key_bytes = bytes.fromhex(public_key_hex[2:])
    address_bytes = keccak(public_key_bytes)[-20:]
    return '0x' + address_bytes.hex()

def _message_hash(payload):
    payload_hash = keccak(text=payload)
    prefix = b"\x19Ethereum Signed Message:\n32"
    return keccak(prefix + payload_hash)

def _addr_recover(msg, signature_hex):
    if not signature_hex.startswith('0x'):
        signature_hex = '0x' + signature_hex
    msg_hash = _message_hash(msg)
    msg_hash_hex = '0x' + msg_hash.hex()
    public_key_hex = _ecdsa_recover(msg_hash_hex, signature_hex)
    if not public_key_hex:
        return False
    recovered = _pubkey_to_address(public_key_hex)
    return recovered.lower()

def _resolve_account(addr):
    addr = addr.lower()
    assert len(addr) <= 42
    if len(addr) == 42:
        assert addr.startswith('0x')
        assert set(addr[2:]) <= set(string.digits + 'abcdef')
    else:
        assert len(addr) > 4

    if len(addr) == 42:
        return handle_lookup(addr)
    return addr

def _check_tick(tick):
    assert type(tick) is str
    assert len(tick) > 0 and len(tick) < 42
    assert tick[0] in string.ascii_uppercase
    assert set(tick) <= set(string.ascii_uppercase + string.digits + '_')


def _get_pubkey(privacy_tick):
    pub, _ = get(privacy_tick, 'privacy_pub', None)
    if pub is None:
        return None
    return int(pub)


def privacy_init(info, args):
    assert args['f'] == 'privacy_init'

    tick = args['a'][0]
    _check_tick(tick)
    privacy_tick = args['a'][1]
    _check_tick(privacy_tick)
    provider_addr = args['a'][2]
    paillier_pub = int(args['a'][3])

    sender = info['sender']

    existing_provider, _ = get(privacy_tick, 'privacy_provider', None)
    if existing_provider is not None:
        return

    put(provider_addr, privacy_tick, 'tick', tick)
    put(provider_addr, privacy_tick, 'transaction_count', 0)
    put(provider_addr, privacy_tick, 'privacy_provider', provider_addr)
    put(provider_addr, privacy_tick, 'privacy_pub', int(paillier_pub))


# def privacy_update(info, args):
#     assert args['f'] == 'privacy_update'


def privacy_deposit(info, args):
    assert args['f'] == 'privacy_deposit'

    privacy_tick = args['a'][0]
    _check_tick(privacy_tick)
    tick, _ = get(privacy_tick, 'tick', None)
    _check_tick(tick)

    functions, _ = get('asset', 'functions', [], tick)
    assert args['f'] in functions
    functions, _ = get('asset', 'functions', [], privacy_tick)
    assert args['f'] in functions

    sender = info['sender']
    addr = handle_lookup(sender)

    existing_deposit, _ = get(privacy_tick, 'privacy_deposit', None, addr)
    if existing_deposit:
        return

    amount = int(args['a'][1])
    assert amount >= 0

    amount_cipher = int(args['a'][2])
    assert amount_cipher >= 0

    balance, _ = get(tick, 'balance', 0, f'{sender}')
    assert balance >= amount
    balance_updated = balance - amount
    put(sender, tick, 'balance', balance_updated, f'{sender}')

    transaction_id, privacy_tick_owner = get(privacy_tick, 'transaction_count', 0)
    transaction_id += 1
    put(privacy_tick_owner, privacy_tick, 'transaction_count', transaction_id)

    put(addr, privacy_tick, 'privacy_deposit', f'{str(amount)},{str(amount_cipher)},{str(transaction_id)}', f'{addr}')
    event('PrivacyDeposit', [privacy_tick, addr, amount, amount_cipher, transaction_id])


# def privacy_deposit_cancel(info, args):
#     assert args['f'] == 'privacy_deposit_cancel'

#     privacy_tick = args['a'][0]
#     _check_tick(privacy_tick)
#     tick, _ = get(privacy_tick, 'tick', None)
#     _check_tick(tick)

#     functions, _ = get('asset', 'functions', [], tick)
#     assert args['f'] in functions
#     functions, _ = get('asset', 'functions', [], privacy_tick)
#     assert args['f'] in functions

#     sender = info['sender']
#     addr = handle_lookup(sender)

#     deposit_info, _ = get(privacy_tick, 'privacy_deposit', None, addr)
#     if not deposit_info:
#         return

#     parts = deposit_info.split(',')
#     assert len(parts) == 3
#     amount = int(parts[0])
#     amount_cipher = int(parts[1])
#     transaction_id = int(parts[2])

#     balance, _ = get(tick, 'balance', 0, sender)
#     balance_updated = balance + amount
#     put(sender, tick, 'balance', balance_updated, sender)

#     put(addr, privacy_tick, 'privacy_deposit', None, addr)

#     event('PrivacyDepositCancel', [privacy_tick, addr, amount, amount_cipher, transaction_id])


# def privacy_enter(info, args):
#     assert args['f'] == 'privacy_enter'

#     privacy_tick = args['a'][0]
#     _check_tick(privacy_tick)
#     tick, _ = get(privacy_tick, 'tick', None)
#     _check_tick(tick)

#     functions, _ = get('asset', 'functions', [], privacy_tick)
#     assert args['f'] in functions
#     functions, _ = get('asset', 'functions', [], tick)
#     assert args['f'] in functions

#     sender = info['sender']
#     transaction_id = int(args['a'][1])
#     signature_hex = args['a'][2]

#     pub = _get_pubkey(privacy_tick)
#     assert pub is not None

#     deposit_info, owner = get(privacy_tick, 'privacy_deposit', 0, f'{sender}')
#     assert deposit_info is not None
#     parts = deposit_info.split(',')
#     assert len(parts) == 3
#     amount = int(parts[0])
#     amount_cipher = int(parts[1])
#     tx_id = int(parts[2])
#     assert tx_id == transaction_id
#     put(owner, privacy_tick, 'privacy_deposit', None, f'{sender}')

#     provider_addr, _ = get(privacy_tick, 'privacy_provider', None)
#     msg_to_sign = f'{privacy_tick},privacy_deposit,{str(amount)},{str(amount_cipher)},{str(transaction_id)}'

#     if provider_addr.lower() != _addr_recover(msg_to_sign, signature_hex):
#         return

#     balance, _ = get(tick, 'balance', 0, f'{privacy_tick}')
#     assert balance >= 0
#     balance_updated = balance + amount
#     put(sender, tick, 'balance', balance_updated, f'{privacy_tick}')

#     balance_cipher, _ = get(privacy_tick, 'privacy_balance', 1, f'{sender},1')
#     balance_cipher_updated = _homomorphic_add(pub, int(balance_cipher), amount_cipher)
#     put(sender, privacy_tick, 'privacy_balance', balance_cipher_updated, f'{sender},1')

#     event('PrivacyEnter', [tick, sender, balance_cipher_updated])


def privacy_withdraw(info, args):
    assert args['f'] == 'privacy_withdraw'

    privacy_tick = args['a'][0]
    _check_tick(privacy_tick)
    functions, _ = get('asset', 'functions', [], privacy_tick)
    assert args['f'] in functions

    sender = info['sender']
    from_addr = handle_lookup(sender)

    existing_withdraw, _ = get(privacy_tick, 'privacy_withdraw', None, from_addr)
    if existing_withdraw:
        return

    # to_addr = _resolve_account(args['a'][1])
    amount = int(args['a'][1])
    amount_cipher = int(args['a'][2])

    pub = _get_pubkey(privacy_tick)
    assert pub is not None

    balance_key = f'{from_addr},1'
    balance_cipher, _ = get(privacy_tick, 'privacy_balance', 1, balance_key)
    
    balance_cipher_updated = _homomorphic_sub(pub, int(balance_cipher), amount_cipher)
    put(sender, privacy_tick, 'privacy_balance', balance_cipher_updated, balance_key)

    transaction_id, privacy_tick_owner = get(privacy_tick, 'transaction_count', 0)
    transaction_id += 1
    put(privacy_tick_owner, privacy_tick, 'transaction_count', transaction_id)

    put(sender, privacy_tick, 'privacy_withdraw', f'{str(balance_cipher)},{str(amount)},{str(amount_cipher)},{str(transaction_id)}', from_addr)

    event('PrivacyWithdraw', [privacy_tick, balance_cipher, amount, amount_cipher, transaction_id])


# def privacy_withdraw_cancel(info, args):
#     assert args['f'] == 'privacy_withdraw_cancel'

#     privacy_tick = args['a'][0]
#     _check_tick(privacy_tick)
#     functions, _ = get('asset', 'functions', [], privacy_tick)
#     assert args['f'] in functions

#     sender = info['sender']
#     from_addr = handle_lookup(sender)

#     withdraw_info, _ = get(privacy_tick, 'privacy_withdraw', None, from_addr)
#     if not withdraw_info:
#         return

#     pub = _get_pubkey(privacy_tick)
#     assert pub is not None

#     parts = withdraw_info.split(',')
#     assert len(parts) == 4
#     addr = parts[0]
#     amount = int(parts[1])
#     amount_cipher = int(parts[2])
#     transaction_id = int(parts[3])

#     balance_key = f'{from_addr},1'
#     balance_cipher, _ = get(privacy_tick, 'privacy_balance', 1, balance_key)
#     balance_cipher_updated = _homomorphic_add(pub, int(balance_cipher), amount_cipher)
#     put(sender, privacy_tick, 'privacy_balance', balance_cipher_updated, balance_key)

#     put(sender, privacy_tick, 'privacy_withdraw', None, from_addr)

#     event('PrivacyWithdrawCancel', [privacy_tick, from_addr, amount, amount_cipher, transaction_id])


# def privacy_exit(info, args):
#     assert args['f'] == 'privacy_exit'

#     privacy_tick = args['a'][0]
#     _check_tick(privacy_tick)
#     tick, _ = get(privacy_tick, 'tick', None)
#     _check_tick(tick)

#     functions, _ = get('asset', 'functions', [], tick)
#     assert args['f'] in functions
#     functions, _ = get('asset', 'functions', [], privacy_tick)
#     assert args['f'] in functions

#     sender = info['sender']
#     transaction_id = int(args['a'][1])
#     signature_hex = args['a'][2]

#     withdraw_info, _ = get(privacy_tick, 'privacy_withdraw', None, sender)
#     if not withdraw_info:
#         return

#     parts = withdraw_info.split(',')
#     assert len(parts) == 4
#     balance_cipher = parts[0]
#     amount = int(parts[1])
#     amount_cipher = int(parts[2])
#     tx_id = int(parts[3])
#     assert tx_id == transaction_id

#     provider_addr, _ = get(privacy_tick, 'privacy_provider', None)
#     msg_to_sign = f'{privacy_tick},privacy_withdraw,{str(amount)},{str(transaction_id)}'

#     if provider_addr.lower() != _addr_recover(msg_to_sign, signature_hex):
#         return

#     pool_balance, _ = get(tick, 'balance', 0, privacy_tick)
#     assert pool_balance >= amount
#     put(sender, tick, 'balance', pool_balance - amount, privacy_tick)

#     balance, _ = get(tick, 'balance', 0, sender)
#     put(sender, tick, 'balance', balance + amount, sender)

#     put(sender, privacy_tick, 'privacy_withdraw', None, sender)

#     event('PrivacyExit', [privacy_tick, sender, amount_cipher])


def privacy_transfer(info, args):
    assert args['f'] == 'privacy_transfer'

    privacy_tick = args['a'][0]
    _check_tick(privacy_tick)
    functions, _ = get('asset', 'functions', [], privacy_tick)
    assert args['f'] in functions

    sender = info['sender']
    from_addr = handle_lookup(sender)
    from_subaccount = int(args['a'][1])
    assert from_subaccount > 0
    to_addr = _resolve_account(args['a'][2])
    to_subaccount = int(args['a'][3])
    assert to_subaccount > 0
    amount_cipher = int(args['a'][4])

    send_info, _ = get(privacy_tick, 'privacy_transfer', None, f'{from_addr},{str(from_subaccount)}')
    if send_info:
        return

    pub = _get_pubkey(privacy_tick)
    assert pub is not None

    balance_cipher, _ = get(privacy_tick, 'privacy_balance', from_subaccount, f'{from_addr},{str(from_subaccount)}')
    balance_cipher_updated = _homomorphic_sub(pub, int(balance_cipher), amount_cipher)
    put(sender, privacy_tick, 'privacy_balance', balance_cipher_updated, f'{from_addr},{str(from_subaccount)}')

    transaction_id, privacy_tick_owner = get(privacy_tick, 'transaction_count', 0)
    transaction_id += 1
    put(privacy_tick_owner, privacy_tick, 'transaction_count', transaction_id)
    put(sender, privacy_tick, 'privacy_transfer', f'{str(balance_cipher)},{str(amount_cipher)},{to_addr},{str(to_subaccount)},{str(transaction_id)}', f'{sender},{str(from_subaccount)}')

    event('PrivacyTransfer', [privacy_tick, from_addr, from_subaccount, to_addr, to_subaccount, balance_cipher, amount_cipher, transaction_id])


# def privacy_send_cancel(info, args):
#     assert args['f'] == 'privacy_send_cancel'

#     privacy_tick = args['a'][0]
#     _check_tick(privacy_tick)
#     functions, _ = get('asset', 'functions', [], privacy_tick)
#     assert args['f'] in functions

#     sender = info['sender']
#     from_addr = handle_lookup(sender)
#     from_subaccount = int(args['a'][1])
#     assert from_subaccount > 0

#     send_info_key = f'{from_addr},{str(from_subaccount)}'
#     send_info, _ = get(privacy_tick, 'privacy_send', None, send_info_key)
#     if not send_info:
#         return

#     pub = _get_pubkey(privacy_tick)
#     assert pub is not None

#     parts = send_info.split(',')
#     assert len(parts) == 5
#     amount_cipher = int(parts[1])
#     transaction_id = int(parts[4])

#     balance_key = f'{from_addr},{str(from_subaccount)}'
#     balance_cipher, _ = get(privacy_tick, 'privacy_balance', 1, balance_key)
#     balance_cipher_updated = _homomorphic_add(pub, int(balance_cipher), amount_cipher)
#     put(sender, privacy_tick, 'privacy_balance', balance_cipher_updated, balance_key)
#     put(sender, privacy_tick, 'privacy_send', None, send_info_key)

#     event('PrivacySendCancel', [privacy_tick, from_addr, from_subaccount, balance_cipher_updated, amount_cipher, transaction_id])


# def privacy_accept(info, args):
#     assert args['f'] == 'privacy_accept'

#     privacy_tick = args['a'][0]
#     _check_tick(privacy_tick)
#     functions, _ = get('asset', 'functions', [], privacy_tick)
#     assert args['f'] in functions

#     from_addr = _resolve_account(args['a'][1])
#     from_subaccount = int(args['a'][2])
#     assert from_subaccount > 0
#     signature_hex = args['a'][3]
#     to_subaccount = int(args['a'][4])
#     sender = info['sender']

#     send_info, _ = get(privacy_tick, 'privacy_send', None, f'{from_addr},{str(from_subaccount)}')
#     if not send_info:
#         return
#     parts = send_info.split(',')
#     assert len(parts) == 5
#     # senderbalance_cipher = int(parts[0])
#     amount_cipher = int(parts[1])
#     to_addr = parts[2]
#     to_subaccount = int(parts[3])
#     transaction_id = int(parts[4])
#     assert to_addr == sender

#     pub = _get_pubkey(privacy_tick)
#     assert pub is not None

#     provider_addr, _ = get(privacy_tick, 'privacy_provider', None)
#     msg_to_sign = f'{privacy_tick},privacy_send,{from_addr},{str(from_subaccount)},{str(transaction_id)}'
#     if provider_addr.lower() != _addr_recover(msg_to_sign, signature_hex):
#         return

#     balance_cipher, _ = get(privacy_tick, 'privacy_balance', 1, f'{to_addr},{str(to_subaccount)}')
#     balance_cipher_updated = _homomorphic_add(pub, int(balance_cipher), amount_cipher)
#     put(to_addr, privacy_tick, 'privacy_balance', balance_cipher_updated, f'{to_addr},{str(to_subaccount)}')
#     put(from_addr, privacy_tick, 'privacy_send', None, f'{from_addr},{str(from_subaccount)}')

#     event('PrivacyAccept', [privacy_tick, to_subaccount, balance_cipher_updated, amount_cipher, transaction_id])


# def privacy_decline(info, args):
#     assert args['f'] == 'privacy_decline'

#     privacy_tick = args['a'][0]
#     _check_tick(privacy_tick)
#     from_addr = _resolve_account(args['a'][1])
#     from_subaccount = int(args['a'][2])
#     assert from_subaccount > 0
#     sender = info['sender']

#     send_info, _ = get(privacy_tick, 'privacy_send', None, f'{from_addr},{str(from_subaccount)}')
#     if not send_info:
#         return
#     parts = send_info.split(',')
#     assert len(parts) == 5
#     amount_cipher = int(parts[1])
#     to_addr = parts[2]
#     transaction_id = int(parts[4])
#     assert to_addr == sender

#     pub = _get_pubkey(privacy_tick)
#     assert pub is not None

#     balance_cipher, _ = get(privacy_tick, 'privacy_balance', 1, f'{from_addr},{str(from_subaccount)}')
#     balance_cipher_updated = _homomorphic_add(pub, int(balance_cipher), amount_cipher)
#     put(from_addr, privacy_tick, 'privacy_balance', balance_cipher_updated, f'{from_addr},{str(from_subaccount)}')
#     put(from_addr, privacy_tick, 'privacy_send', None, f'{from_addr},{str(from_subaccount)}')

#     event('PrivacyDecline', [privacy_tick, from_addr, from_subaccount, balance_cipher_updated, amount_cipher, transaction_id])

