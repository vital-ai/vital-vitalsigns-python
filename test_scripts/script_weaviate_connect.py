import weaviate


def main():
    print('Hello World')
    # local instance running in docker
    client = weaviate.connect_to_local()

    try:
        meta_info = client.get_meta()
        print(meta_info)

    finally:
        client.close()


if __name__ == "__main__":
    main()
