from typing import TypedDict, Literal, Optional
from datetime import datetime


SEGMENT_STATE_CLASS = Literal[
    "segment_state_class",
    "service_segment_state_class",
]

SEGMENT_STATUS_TYPE = Literal[
    "SEGMENT_STATUS_TYPE_OK",
    "SEGMENT_STATUS_TYPE_UNINITIALIZED",
]

COLLECTIONS_STATUS_TYPE = Literal[
    "COLLECTIONS_STATUS_TYPE_OK",
    "COLLECTIONS_STATUS_TYPE_UNINITIALIZED",
]

VECTOR_STATUS_TYPE = Literal[
    "VECTOR_STATUS_TYPE_INDEXED",
    "VECTOR_STATUS_TYPE_UNINITIALIZED",
]

# TODO background thread can periodically update the segment update time
# so every change does not result in a change to the segment object

class SegmentState(TypedDict):

    segment_state_class: SEGMENT_STATE_CLASS

    segment_status_type: SEGMENT_STATUS_TYPE

    segment_update_datetime: Optional[datetime]

    has_vector_index: bool

    vector_status_type: Optional[VECTOR_STATUS_TYPE]

    vector_index_update_datetime: Optional[datetime]

# service graph itself does not have its objects in the vector store

class ServiceSegmentState(SegmentState):

    # for SERVICE_GRAPH True if graph db is associated with vector store
    has_vector_collections: bool

    # for SERVICE_GRAPH, track if collections are init-ed
    collections_status_type: Optional[COLLECTIONS_STATUS_TYPE]


