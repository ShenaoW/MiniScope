from hashlib import sha256


def calc_sha256(data: str) -> str:
    """
    计算字符串的 SHA-256 值

    @param data: 待计算的字符串
    :return: SHA-256 值
    """
    return sha256(data.encode('utf-8')).hexdigest()