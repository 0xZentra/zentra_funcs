# tools
import string

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
    witness_addr = args['a'][4].lower() # 新增见证人地址

    sender = info['sender']

    existing_provider, _ = get(privacy_tick, 'privacy_provider', None)
    if existing_provider is not None:
        return

    put(provider_addr, privacy_tick, 'tick', tick)
    put(provider_addr, privacy_tick, 'transaction_count', 0)
    put(provider_addr, privacy_tick, 'privacy_provider', provider_addr)
    put(provider_addr, privacy_tick, 'privacy_pub', int(paillier_pub))
    put(provider_addr, privacy_tick, 'witness_role', witness_addr) # 存入见证人地址
    put(provider_addr, privacy_tick, 'total_supply', 0) # 初始化总供应量
    event('PrivacyInitSuccess', [privacy_tick, witness_addr, paillier_pub])

# privacy_lite_v2_withdraw
def privacy_v2_withdraw(info, args):
    assert args['f'] == 'privacy_v2_withdraw'

    privacy_tick = args['a'][0]
    _check_tick(privacy_tick)
    functions, _ = get('asset', 'functions', [], privacy_tick)
    assert args['f'] in functions

    amount = int(args['a'][1])
    assert amount > 0
    amount_cipher = int(args['a'][2])
    assert amount_cipher > 0
    old_balance_cipher = int(args['a'][3])
    assert old_balance_cipher > 0
    nonce = int(args['a'][4]) 
    signature = args['a'][5]

    sender = info['sender'].lower()

    # 读取witness_addr进行签名校验
    witness, _ = get(privacy_tick, 'witness_role', None)
    assert witness is not None, "Witness not initialized"

    # nonce校验，防重放
    stored_nonce, _ = get(privacy_tick,'privacy_nonce', 0, sender)
    assert nonce == int(stored_nonce) + 1, "Invalid nonce"

    # 签名校验
    msg = f"{privacy_tick},withdraw,{sender},{nonce},{amount},{amount_cipher},{old_balance_cipher}"
    recovered_addr = _addr_recover(msg,signature)
    assert recovered_addr == witness.lower(), "Invalid signature"

    # 获取同态公钥
    pub = _get_pubkey(privacy_tick)
    assert pub is not None

    # 读取并校验链上状态
    stored_balance, _ = get(privacy_tick, 'privacy_balance', 1, sender)
    assert int(stored_balance) == old_balance_cipher, "State mismatch"

    total_supply, _ = get(privacy_tick, 'total_supply', 0)
    new_total = int(total_supply) - amount
    assert new_total >= 0, "Insufficent total supply"

    # 执行同态减法
    new_balance_cipher = _homomorphic_sub(pub, int(stored_balance), amount_cipher)

    # 更新
    put(sender, privacy_tick, 'privacy_balance', new_balance_cipher, sender)
    put(sender, privacy_tick, 'privacy_nonce', nonce, sender)
    put(sender, privacy_tick, 'total_supply', new_total)

    event('PrivacyWithdrawSuccess', [sender, amount, new_balance_cipher, nonce])

    return "SUCCESS"
