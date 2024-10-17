from typing_extensions import TypedDict
from vital_ai_vitalsigns.metaql.metaql_query import MetaQLQuery


class MetaQLRequest(TypedDict):

    metaql_class: str

    account_uri: str
    account_id: str
    login_uri: str

    jwt_str: str

    metaql_query: MetaQLQuery


