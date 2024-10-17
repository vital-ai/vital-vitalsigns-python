from typing import Literal, Optional

from typing_extensions import TypedDict

OK_STATUS_TYPE = "OK_STATUS_TYPE"
ERROR_STATUS_TYPE = "ERROR_STATUS_TYPE"
FAILURE_STATUS_TYPE = "FAILURE_STATUS_TYPE"

STATUS_TYPE = Literal[
    "OK_STATUS_TYPE",
    "ERROR_STATUS_TYPE",
    "FAILURE_STATUS_TYPE"
]


class MetaQLStatus(TypedDict):

    metaql_class: str

    status_type: STATUS_TYPE
    status_code: int
    status_message: Optional[str]
