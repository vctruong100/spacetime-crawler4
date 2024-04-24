import hashlib

def simhash(wordcnts):
    """
    Compute the simhash fingerprint of a document.
    :param wordcnts: A dictionary of word counts.
    :return: The simhash fingerprint of the document.
    """
    # Size of the hash vector
    hash_size = 8
    v = [0] * hash_size

    for word, cnt in wordcnts.items():
        # Create binary hash of the word
        word_hash = hash(word) % (2 ** hash_size)
        binary_hash = format(word_hash, f'0{hash_size}b')

        # Update the simhash fingerprint
        for i in range(hash_size):
            bit_value = 1 if binary_hash[i] == '1' else -1
            v[i] += bit_value * cnt # update the vector with the word count multiplied by the bit value (1/0)

    # Form simhash fingerprint by converting the vector to a binary string
    fingerprint = ''.join(['1' if i > 0 else '0' for i in v]) # append 1 if positive or 0 otherwise

    return int(fingerprint, 2) # convert the binary string to a binary integer

def hamming_distance(hash1, hash2):
    """
    Compute the hamming distance between two hashes.
    :param hash1: The first hash.
    :param hash2: The second hash.
    :return: The hamming distance between the two hashes.
    """
    return bin(hash1 ^ hash2).count('1') # count the number of bits that differ between the two hashes