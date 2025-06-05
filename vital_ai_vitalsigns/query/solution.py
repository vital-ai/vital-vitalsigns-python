from enum import Enum
from typing import TypeVar, Dict

G = TypeVar('G', bound='GraphObject')


# TODO replace with URI constants
class SolutionConst(Enum):
    UNKNOWN = 'urn:solution_unknown'
    NOT_EXIST = 'urn:solution_not_exist'


class Solution:

    # contains two mappings:

    # mapping of binding variable to URI

    # mapping of binding variable to graph object
    # if graph object has not been retrieved it is unknown
    # if an attempt to retrieve it was made and it was determined that
    # the underlying graph objects does not exist, then it is
    # not exist

    # an instance of GraphMatch may contain the same information
    # and is serializable
    # Solution is meant to be a friendly interface when additional serialization
    # is not necessary

    def __init__(self,
                 uri_map: Dict[str, str | SolutionConst] = None,
                 object_map: Dict[str, G | SolutionConst] = None,
                 root_binding: str | None = None,
                 root_object: G | None = None,
                 ):

        if uri_map is None:
            uri_map = {}

        if object_map is None:
            object_map = {}

        self.uri_map = uri_map
        self.object_map = object_map
        self.root_binding = root_binding
        self.root_object = root_object


