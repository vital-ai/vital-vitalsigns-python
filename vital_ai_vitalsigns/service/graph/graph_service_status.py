from enum import Enum

class GraphServiceStatusType(Enum):
    UNINITIALIZED = "GraphServiceStatusType_UNINITIALIZED"
    READY = "GraphServiceStatusType_READY"
    CONNECTION_ERROR = "GraphServiceStatusType_CONNECTION_ERROR"

class GraphServiceStatus:
    def __init__(self, status: GraphServiceStatusType = GraphServiceStatusType.UNINITIALIZED, message: str = None):
        self.status_type = status
        self.status_message = message

    def get_status_type(self) -> GraphServiceStatusType:
        return self.status_type

    def get_status_message(self) -> str:
        return self.status_message
