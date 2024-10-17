from typing import List
from typing_extensions import TypedDict
from vital_ai_vitalsigns.metaql.metaql_result_list import MetaQLResultList
from vital_ai_vitalsigns.metaql.metaql_status import MetaQLStatus


class MetaQLResponse(TypedDict):

    metaql_class: str

    result_status: MetaQLStatus

    result_list: MetaQLResultList

