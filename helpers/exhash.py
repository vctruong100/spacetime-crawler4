# helpers/exhash.py
#
# uses crc32 checksum and the content size to compute
# the exact hash of a page
# returns as a hexadecimal hash without the '0x' prefix
#
# { i32, i32 } => 64 bits

from helpers.crc32 import crc32

def exhash(content, size):
    """Computes the exhash of a page given its content in bytes
    and its content size.

    :param content: Content in bytes
    :param size: How many bytes content is
    :return: A hex string of the hash
    :rtype: str
    """
    crc = crc32(content)
    exhash = bytearray(8)
    for i in range(4):
        exhash[i] = crc & (0xFF << (i << 3))
    for i in range(4):
        exhash[4 + i] = size & (0xFF << (i << 3))
    return exhash.hex()

