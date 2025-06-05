from typing import MutableSequence, TypeVar, List, Optional, Iterator, Any
from vital_ai_vitalsigns.collection.graph_collection import GraphCollection
from vital_ai_vitalsigns.model.GraphObject import GraphObject


G = TypeVar('G', bound=Optional[GraphObject])


class GraphPart(MutableSequence[G]):
    def __init__(self, data: List[G] = None, score: float = 1.0, *, graph_collection: GraphCollection | None = None):
        self._data = data
        self._graph_collection = graph_collection
        self._uri_map = {}
        self._score = score

    def __iter__(self) -> Iterator[G]:
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __getitem__(self, index) -> G:
        return self._data[index]

    def __setitem__(self, index, value: G):

        if not isinstance(value, GraphObject):
            raise ValueError("All items must be instances of GraphObject or its subclasses")

        if hasattr(self._data[index], 'URI'):
            self._uri_map.pop(self._data[index].URI, None)

        if hasattr(value, 'URI'):
            self._uri_map[value.URI] = value

        self._data[index] = value

    def __delitem__(self, index):

        if hasattr(self._data[index], 'URI'):
            self._uri_map.pop(self._data[index].URI, None)

        del self._data[index]

    def insert(self, index, value: G):

        if not isinstance(value, GraphObject):
            raise ValueError("All items must be instances of GraphObject or its subclasses")

        self.pop(value.URI)

        if hasattr(value, 'URI'):
            self._uri_map[value.URI] = value

        self._data.insert(index, value)

    def get(self, uri, default=None):

        for item in self._data:
            if item.URI == uri:
                return item

        return default

    def pop(self, uri, default=None):

        for i, item in enumerate(self._data):

            if item.URI == uri:

                return self._data.pop(i)  # Removes and returns the item

        if default is not None:
            return default

        return None

    def remove(self, uri, default=None):
        return self.pop(uri, default)

    def add(self, obj: G):

        if not isinstance(obj, GraphObject):
            raise ValueError("Item must be instances of GraphObject or its subclasses")

        self.pop(obj.URI)

        self._data.append(obj)

    def add_objects(self, objects: List[G]):

        if not all(isinstance(obj, GraphObject) for obj in objects):
            raise ValueError("All items must be instances of GraphObject or its subclasses")

        for obj in objects:

            self.pop(obj.URI)
            self._data.append(obj)

    def remove_objects(self, uris: List[str]):
        """Remove objects from the part by a list of URI values."""
        to_remove_indexes = []
        for uri in uris:
            for i, item in enumerate(self._data):
                if item.URI == uri:
                    to_remove_indexes.append(i)
                    break  # Assuming URIs are unique, stop after finding the first match

        # Iterate in reverse order to avoid altering the indexes of items to be removed
        for i in sorted(to_remove_indexes, reverse=True):
            del self._data[i]

    def set_score(self, score: float):
        self._score = score

    def get_score(self) -> float:
        return self._score

# hold a small number of graph elements which are related
# such as those representing an entity, a document, or a relation

# this is different than a collection in that collection is meant
# for larger or complete graphs which are indexed and queryable

# GraphPart may be used as a return type to return the specific graph elements
# of the part (or partition)
# such as a get_entity() method which returns the nodes and edges
# that represent that entity

# GraphPart may be treated as a "view" on an underlying Graph Collection
# this would mean a change to an object like a node representing an entity
# would be reflected in GraphParts that reference that node
# in this case the GraphPart is mainly a list of URIs with the objects
# stored within the Graph Collection
