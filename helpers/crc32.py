# helpers/crc32.py
#
# cyclic redundancy check
# used to compute an exact hash of the text content
#
# collisions might happen so bytes should use
# an additional discriminator

# used this article to guide the implementation of crc32:
# https://www.sunshine2k.de/articles/coding/crc/understanding_crc.html

CRC32_POLY = 0xEDB88320 # reversed (LSB first; little endian)
CRC32_LOOKUP = [0] * 256 # allocate 256 entries


# pre-compute byte lookup table
# each byte is divided by the CRC32 polynomial
# the result is a 32-bit remainder
#
# because xors are commutative, we can divide the input byte
# then xor the next input byte, and repeatedly without affecting the
# final result
#
# NOTE: this assumes the polynomial is reversed LSB first (which it is)
for i in range(0x00, 0x100):
    val = i
    for _ in range(8):
        if 1 == (val & 1):
            # LSB set
            val >>= 1
            val ^= CRC32_POLY
        else:
            val >>= 1
    CRC32_LOOKUP[i] = val


# CRC32/ISO-HDLC
# https://reveng.sourceforge.io/crc-catalogue/all.html#crc.cat.crc-32-iso-hdlc
#
# also called crc32b
# byte lookup table matches with actual crc32 computation
# (i.e. LSB first vs LSB first)
def crc32(bytes):
    """Computes a cyclic redundancy check of 32 bits.
    Returns the hash value as an unsigned 32-bit integer.

    :param bytes: A bytes or bytearray object
    :return: A crc32 remainder (a 32 bit integer)
    :rtype: int
    """
    crc = 0xFFFFFFFF
    for b in bytes:
        crc ^= b
        i = crc & 0xFF
        # after dividing, the first 8 bits are zeroed
        crc = (crc >> 8) ^ CRC32_LOOKUP[i]
    return crc ^ 0xFFFFFFFF

