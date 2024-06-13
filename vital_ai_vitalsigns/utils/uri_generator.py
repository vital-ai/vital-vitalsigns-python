import uuid


class URIGenerator:
    org = 'vital.ai'
    app = 'vitalsigns'
    base_uri = 'http://vital.ai/' + org + '/' + app + '/'

    @classmethod
    def generate_uri(cls) -> str:
        unique_id = str(uuid.uuid4())
        uri = cls.base_uri + unique_id
        return uri

