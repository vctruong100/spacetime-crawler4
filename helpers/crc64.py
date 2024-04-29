# helpers/crc64.py
#
# extended from helpers/crc32.py
# see crc32 file for more details

CRC64_POLY = 0xc96c5795d7870f42 # reversed (LSB first; little endian)
CRC64_LOOKUP = [0] * 256 # allocate 256 entries

for i in range(0x00, 0x100):
    val = i
    for _ in range(8):
        if 1 == (val & 1):
            # LSB set
            val >>= 1
            val ^= CRC64_POLY
        else:
            val >>= 1
    CRC64_LOOKUP[i] = val


# CRC64/XZ
# https://reveng.sourceforge.io/crc-catalogue/all.htm#crc.cat.crc-64-xz
def crc64(bytes):
    """Computes a cyclic redundancy check of 64 bits.
    Returns the hash value as an unsigned 64-bit integer.

    :param bytes: A bytes or bytearray object
    :return: A crc64 remainder (a 64 bit integer)
    :rtype: int
    """
    crc = 0xFFFFFFFFFFFFFFFF
    for b in bytes:
        crc ^= b
        i = crc & 0xFF
        # after dividing, the first 8 bits are zeroed
        crc = (crc >> 8) ^ CRC64_LOOKUP[i]
    return crc ^ 0xFFFFFFFFFFFFFFFF

