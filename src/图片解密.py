"""按阅读器容器格式转换图片，私钥和图片内容只保留在内存中。"""

from __future__ import annotations

import base64
import json
from urllib.parse import parse_qs, unquote, urlsplit

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.hashes import SHA512
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class 图片解密错误(RuntimeError):
    """图片容器或密钥不符合支持的格式。"""


def 解码Base64URL(内容: str) -> bytes:
    """解码JWK字段使用的无填充Base64URL。"""
    return base64.urlsafe_b64decode(内容 + "=" * (-len(内容) % 4))


def 计算共享密钥(私钥文本: str, 公钥字节: bytes) -> bytes:
    """使用阅读器临时P-256私钥计算共享密钥。"""
    try:
        私钥数据 = json.loads(base64.b64decode(私钥文本, validate=True))
        if 私钥数据.get("kty") != "EC" or 私钥数据.get("crv") != "P-256":
            raise ValueError("密钥类型不匹配")
        私钥值 = int.from_bytes(解码Base64URL(私钥数据["d"]), "big")
        私钥 = ec.derive_private_key(私钥值, ec.SECP256R1())
        公钥 = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), 公钥字节)
        共享密钥 = 私钥.exchange(ec.ECDH(), 公钥)
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as e:
        raise 图片解密错误("图片密钥无效。") from e
    if len(共享密钥) != 32:
        raise 图片解密错误("图片共享密钥长度不正确。")
    return 共享密钥


def 读取参数(地址: str, 版本: int) -> tuple[bytes, bytes | None, int | None]:
    """读取签名地址中的IV、GCM盐和时间戳。"""
    部件 = urlsplit(地址)
    if 部件.scheme != "https" or not (
        部件.hostname and 部件.hostname.endswith(".hdslb.com")
    ):
        raise 图片解密错误("图片地址不是受支持的HTTPS漫画资源。")
    参数 = parse_qs(部件.query)
    try:
        编码参数 = 参数["cpx"][0]
        if 版本 != 8:
            编码参数 = unquote(编码参数)
        解码参数 = base64.b64decode(编码参数, validate=True)
    except (KeyError, ValueError) as e:
        raise 图片解密错误("图片地址缺少有效加密参数。") from e
    起点 = {3: 26, 5: 33, 6: 34, 7: 26, 8: 32}[版本] - 1
    if len(解码参数) < 起点 + 16:
        raise 图片解密错误("图片加密参数不完整。")
    盐 = 解码参数[48:64] if 版本 == 5 else None
    时间戳 = None
    if 版本 == 8:
        try:
            时间戳 = int(参数["ts"][0][-8:], 16)
        except (KeyError, ValueError) as e:
            raise 图片解密错误("图片地址缺少有效时间戳。") from e
    return 解码参数[起点 : 起点 + 16], 盐, 时间戳


def 拆分容器(内容: bytes, 版本: int, 时间戳: int | None) -> tuple[bytes, bytes]:
    """移除容器元数据并恢复服务器公钥和加密负载。"""
    if 版本 != 8:
        if len(内容) < 71:
            raise 图片解密错误("图片容器不完整。")
        长度 = int.from_bytes(内容[1:5], "big")
        if 长度 <= 0 or 长度 + 70 != len(内容):
            raise 图片解密错误("图片容器声明长度不正确。")
        return 内容[5 : 长度 + 5], 内容[长度 + 5 :]

    if 时间戳 is None:
        raise 图片解密错误("第8版图片容器缺少时间戳。")
    负载长度 = len(内容) - 70
    if 负载长度 < 69:
        raise 图片解密错误("图片容器不完整。")
    状态 = (时间戳 - 负载长度 - 69) % 4294967296
    位置集合: set[int] = set()
    while len(位置集合) < 69:
        状态 = (状态 * 1664525 + 1013904223) % 4294967296
        位置集合.add(状态 * 负载长度 // 4294967296)
    公钥部分 = []
    负载部分 = []
    上一位置 = 1
    for 序号, 位置 in enumerate(sorted(位置集合)):
        偏移 = 位置 + 1
        负载部分.append(内容[上一位置:偏移])
        if 序号 >= 4:
            公钥部分.append(内容[偏移 : 偏移 + 1])
        上一位置 = 偏移 + 1
    负载部分.append(内容[上一位置:])
    公钥 = b"".join(公钥部分)
    if len(公钥) != 65 or not 公钥.startswith(b"\x04"):
        raise 图片解密错误("图片容器中的P-256公钥无效。")
    return b"".join(负载部分), 公钥


def CTR解密(密钥: bytes, IV: bytes, 负载: bytes, 完整计数器: bool) -> bytes:
    """解密图片前缀并保留未加密的剩余内容。"""
    长度 = min(len(负载), 25 * 1024)
    计数器值 = int.from_bytes(IV, "big")
    输出 = bytearray(长度)
    for 起点 in range(0, 长度, 16):
        加密器 = Cipher(algorithms.AES(密钥), modes.ECB()).encryptor()
        块序号 = 起点 // 16
        if 完整计数器:
            当前计数器 = (计数器值 + 块序号) % (1 << 128)
        else:
            高位 = 计数器值 & ~((1 << 64) - 1)
            当前计数器 = 高位 | ((计数器值 + 块序号) & ((1 << 64) - 1))
        密钥流 = 加密器.update(当前计数器.to_bytes(16, "big")) + 加密器.finalize()
        块 = 负载[起点 : min(起点 + 16, 长度)]
        输出[起点 : 起点 + len(块)] = bytes(a ^ b for a, b in zip(块, 密钥流))
    return bytes(输出) + 负载[长度:]


def CBC解密(密钥: bytes, IV: bytes, 负载: bytes) -> bytes:
    """解密第6版容器的CBC前缀。"""
    长度 = min(len(负载), 21 * 1024 + 16)
    if not 长度 or 长度 % 16:
        raise 图片解密错误("CBC图片前缀长度不正确。")
    解密器 = Cipher(algorithms.AES(密钥), modes.CBC(IV)).decryptor()
    明文 = 解密器.update(负载[:长度]) + 解密器.finalize()
    填充 = 明文[-1]
    if not 1 <= 填充 <= 16 or 明文[-填充:] != bytes([填充]) * 填充:
        raise 图片解密错误("CBC图片填充无效。")
    return 明文[:-填充] + 负载[长度:]


def GCM解密(密钥: bytes, IV: bytes, 盐: bytes, 负载: bytes) -> bytes:
    """解密第5版容器的GCM前缀。"""
    长度 = min(len(负载), 30 * 1024 + 16)
    if 长度 < 16:
        raise 图片解密错误("GCM图片前缀不完整。")
    派生密钥 = PBKDF2HMAC(algorithm=SHA512(), length=32, salt=盐, iterations=100000).derive(密钥)
    return AESGCM(派生密钥).decrypt(IV, 负载[:长度], 盐) + 负载[长度:]


def 解密图片(私钥文本: str, 内容: bytes, 地址: str) -> bytes:
    """转换阅读器第3、5、6、7、8版加密图片。"""
    if not 内容 or len(内容) > 32 * 1024 * 1024:
        raise 图片解密错误("图片容器为空或超过大小限制。")
    版本 = 内容[0]
    if 版本 not in {3, 5, 6, 7, 8}:
        raise 图片解密错误(f"不支持第{版本}版图片容器。")
    IV, 盐, 时间戳 = 读取参数(地址, 版本)
    负载, 公钥 = 拆分容器(内容, 版本, 时间戳)
    共享密钥 = 计算共享密钥(私钥文本, 公钥)
    try:
        if 版本 == 6:
            return CBC解密(共享密钥, IV, 负载)
        if 版本 == 5:
            if 盐 is None:
                raise 图片解密错误("GCM图片缺少盐。")
            return GCM解密(共享密钥, IV, 盐, 负载)
        return CTR解密(共享密钥, IV, 负载, 版本 == 8)
    except ValueError as e:
        raise 图片解密错误("图片内容转换失败。") from e
