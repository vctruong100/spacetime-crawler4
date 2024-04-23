import hashlib

def simhash(wordcnts, hashbits=128):
    """
    Compute the simhash fingerprint of a page.    
    :param wordcnts: A dictionary of word counts.
    :param hashbits: The number of bits in the fingerprint.
    :return: The simhash fingerprint.
    
    """
    
    # Initialize the simhash fingerprint
    simhash = [0] * hashbits

    for word, cnt in wordcnts.items():
        # Compute the hash of the word based on the full 256-bit hash
        wordhash = int(hashlib.sha256(word.encode('utf-8')).hexdigest(), 16)

        # Update the simhash fingerprint
        for i in range(hashbits):
            # Create a bitmask to isolate the i-th bit
            bitmask = 1 << i
            # Check if the i-th bit is set and update vector
            if wordhash & bitmask:
                simhash[i] += cnt # Add the count if bit is 1
            else:
                simhash[i] -= cnt # Subtract the count if bit is 0

    fingerprint = 0
    for i in range(hashbits):
        if simhash[i] > 0:
            fingerprint |= 1 << i # Set the i-th bit if simhash[i] > 0

    return fingerprint