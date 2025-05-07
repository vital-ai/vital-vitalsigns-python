from datasketch import MinHash, MinHashLSH
from datasketch import MinHashLSHForest


def get_minhash(name):
    m = MinHash(num_perm=128)
    for token in name:
        m.update(token.encode('utf8'))
    return m


def main():
    print('Test DataSketch')

    # Create an LSH index
    lsh_index = MinHashLSH(threshold=0.5, num_perm=128)

    # Dictionary to hold id -> name mapping
    id_to_name = {}

    # List of (id, name) tuples
    data = [
        (1, "Alice"),
        (2, "Alicia"),
        (3, "Bob"),
        (4, "Robert"),
        (5, "Roberta"),
        (6, "Charles"),
        (7, "Charlie")
    ]

    # Insert each name into the LSH index with its identifier
    for idx, name in data:
        minhash = get_minhash(name)
        lsh_index.insert(str(idx), minhash)
        id_to_name[idx] = name

    # Query for the closest matches to a given name
    query_name = "Alic"
    query_minhash = get_minhash(query_name)
    result_ids = lsh_index.query(query_minhash)

    # Retrieve names using the identifiers
    result_names = [id_to_name[int(rid)] for rid in result_ids]

    print(f"Closest matches to '{query_name}': {result_names}")


if __name__ == "__main__":
    main()

