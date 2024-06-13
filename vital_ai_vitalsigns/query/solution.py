from enum import Enum
from typing import TypeVar, Dict

G = TypeVar('G', bound='GraphObject')


# TODO replace with URI constants
class SolutionConst(Enum):
    UNKNOWN = 'solution_unknown'
    NOT_EXISTS = 'solution_not_exists'


class Solution:

    def __init__(self,
                 uri_map: Dict[str, str | SolutionConst] = dict(),
                 object_map: Dict[str, G | SolutionConst] = dict(),
                 root_binding: str | None = None,
                 root_object: G | None = None,
                 ):
        self.uri_map = uri_map
        self.object_map = object_map
        self.root_binding = root_binding
        self.root_object = root_object

    # contains two mappings:

    # mapping of binding variable to URI

    # mapping of binding variable to graph object
    # if graph object has not been retrieved it is unknown
    # if an attempt to retrieve it was made and it was determined that
    # the underlying graph objects does not exists, then it is
    # not exists

    # an instance of GraphMatch may contain the same information
    # and is serializable
    # Solution is meant to be a friendly interface when additional serialization
    # is not necessary

