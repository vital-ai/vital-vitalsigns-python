from collections.abc import MutableSequence
from vital_ai_vitalsigns.collection.rdf_collection_impl import RdfCollectionImpl
from vital_ai_vitalsigns.model.GraphObject import GraphObject
from vital_ai_vitalsigns.model.VITAL_Edge import VITAL_Edge
from vital_ai_vitalsigns.query.result_element import ResultElement
from vital_ai_vitalsigns.query.result_list import ResultList
from vital_ai_vitalsigns.vitalsigns import VitalSigns
from typing import Optional, TypeVar, List, Iterator

G = TypeVar('G', bound=Optional[GraphObject])


class GraphCollection(MutableSequence[G]):

    def __init__(self, data: List[G] | None = None, use_rdfstore: bool = True, use_vectordb: bool = True, embedding_model_id: str = 'paraphrase-MiniLM-L3-v2'):

        self._use_rdfstore = use_rdfstore
        self._use_vectordb = use_vectordb
        self._embedding_model_id = embedding_model_id

        if data is None:
            self._data = []
        else:
            self._data = [item for item in data if isinstance(item, GraphObject)]

        self._uri_map = {}
        self._vector_properties = {}

        if use_vectordb is True:
            from vital_ai_vitalsigns.collection.vector_collection_impl import VectorCollectionImpl
            self._vectordb = VectorCollectionImpl(self)

        if use_rdfstore is True:
            self._rdfstore = RdfCollectionImpl()

        for item in self._data:
            if hasattr(item, 'URI'):

                self._uri_map[item.URI] = item

                if self._use_rdfstore is True:
                    obj_nt = item.to_rdf()
                    self._rdfstore.add_triples(obj_nt)

                if self._use_vectordb is True:
                    embedding_model = VitalSigns.get_embedding_model(self._embedding_model_id)

                    uri = str(item.URI)
                    name = str(item.name)

                    if len(self._vector_properties) == 0:
                        text = name
                    else:
                        text = self.get_object_text(item)

                    encoding = embedding_model.vectorize(text)

                    # todo index data

    def __len__(self):
        return len(self._data)

    def __iter__(self) -> Iterator[G]:
        return iter(self._data)

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

    def get(self, uri, default=None) -> G:

        for item in self._data:
            if item.URI == uri:
                return item

        return default

    def pop(self, uri, default=None):

        for i, item in enumerate(self._data):

            if item.URI == uri:

                if self._use_rdfstore is True:
                    self._rdfstore.delete_triples(uri)

                if self._use_vectordb is True:
                    self._vectordb.remove_doc(uri)

                return self._data.pop(i)  # Removes and returns the item

        if default is not None:
            return default

        # raise ValueError("No item found with the specified URI.")
        return None

    def remove(self, uri, default=None) -> G:
        return self.pop(uri, default)

    def add(self, obj: G):

        if not isinstance(obj, GraphObject):
            raise ValueError("Item must be instances of GraphObject or its subclasses")

        self.pop(obj.URI)

        self._data.append(obj)

        if self._use_vectordb is True:

            vs = VitalSigns()

            embedding_model = vs.get_embedding_model(self._embedding_model_id)

            uri = str(obj.URI)
            name = str(obj.name)
            class_uri = str(obj.get_class_uri())

            if len(self._vector_properties) == 0:
                text = name
            else:
                text = self.get_object_text(obj)

            encoding = embedding_model.vectorize(text)

            # index_docs = [GraphObjectDoc(id=uri, URI=uri, ClassURI=class_uri, name=name, text=text, embedding=encoding)]

            # self._vectordb.index_documents(DocList[GraphObjectDoc](index_docs))

            vector = encoding  # np.array(encoding, dtype=np.float32)
            # vector = vector / np.linalg.norm(vector)
            # vector = vector.reshape(1, -1)

            self._vectordb.index.add_items([vector])

            self._vectordbdoc_id_to_index[uri] = self._vectordb.current_index
            self._vectordb.index_to_doc_id[self._vectordb.current_index] = uri
            self._vectordb.current_index += 1

        if self._use_rdfstore is True:
            obj_nt = obj.to_rdf()
            self._rdfstore.add_triples(obj_nt)

    def add_objects(self, objects: List[G]):

        if not all(isinstance(obj, GraphObject) for obj in objects):
            raise ValueError("All items must be instances of GraphObject or its subclasses")

        for obj in objects:

            self.pop(obj.URI)
            self._data.append(obj)

            if self._use_vectordb is True:

                vs = VitalSigns()

                embedding_model = vs.get_embedding_model(self._embedding_model_id)

                uri = str(obj.URI)
                name = str(obj.name)
                class_uri = str(obj.get_class_uri())

                if len(self._vector_properties) == 0:
                    text = name
                else:
                    text = self.get_object_text(obj)

                encoding = embedding_model.vectorize(text)

                # index_docs = [GraphObjectDoc(id=uri, URI=uri, ClassURI=class_uri, name=name, text=text, embedding=encoding)]

                # self._vectordb.index_documents(DocList[GraphObjectDoc](index_docs))

                vector = encoding  # np.array(encoding, dtype=np.float32)
                # vector = vector / np.linalg.norm(vector)
                # vector = vector.reshape(1, -1)

                self._vectordb.index.add_items([vector])

                self._vectordb.doc_id_to_index[uri] = self._vectordb.current_index
                self._vectordb.index_to_doc_id[self._vectordb.current_index] = uri
                self._vectordb.current_index += 1

            if self._use_rdfstore is True:
                obj_nt = obj.to_rdf()
                self._rdfstore.add_triples(obj_nt)

    def get_object_text(self, obj: G):
        text = ""
        class_uri = obj.get_class_uri()
        for obj_class_uri in self._vector_properties:
            if obj_class_uri == class_uri:
                prop_uri_list = self._vector_properties[obj_class_uri]
                for puri in prop_uri_list:
                    value = obj.get_property_value(puri)
                    text = text + " " + str(value)
                    # print(f"Embedding Text {class_uri} in {puri} {str(value)}")

        return text.strip()

    def remove_objects(self, uris: List[str]):
        """Remove objects from the collection by a list of URI values."""
        to_remove_indexes = []
        for uri in uris:
            for i, item in enumerate(self._data):
                if item.URI == uri:
                    to_remove_indexes.append(i)
                    if self._use_rdfstore is True:
                        self._rdfstore.delete_triples(uri)
                    if self._use_vectordb is True:
                        self._vectordb.remove_doc(uri)
                    break  # Assuming URIs are unique, stop after finding the first match

        # Iterate in reverse order to avoid altering the indexes of items to be removed
        for i in sorted(to_remove_indexes, reverse=True):
            del self._data[i]

    def set_vector_properties(self, class_uri, property_uris: List):
        """Set the vector properties for a given class URI."""
        if not isinstance(property_uris, list):
            raise ValueError("property_uris must be a list")
        self._vector_properties[class_uri] = property_uris

    def get_vector_properties(self, class_uri: str):
        """Get the vector properties for a given class URI."""
        return self._vector_properties.get(class_uri, [])

    def remove_vector_properties(self, class_uri: str):
        """Remove the vector properties for a given class URI."""
        if class_uri in self._vector_properties:
            del self._vector_properties[class_uri]

    def get_vector_class_uris(self):
        return list(self._vector_properties.keys())

    def get_edges_incoming(self, uri: str) -> List[G]:
        incoming_edges = [item for item in self._data if isinstance(item, VITAL_Edge) and item.edgeDestination == uri]
        return incoming_edges

    def get_edges_outgoing(self, uri: str) -> List[G]:
        outgoing_edges = [item for item in self._data if isinstance(item, VITAL_Edge) and item.edgeSource == uri]
        return outgoing_edges

    def get_nodes_incoming(self, uri: str) -> List[G]:
        """
        Return the node objects that have an outgoing edge to the given URI.
        """
        # Use a set to avoid duplicates and collect URIs of source nodes
        incoming_node_uris = {item.edgeSource for item in self._data if
                              isinstance(item, VITAL_Edge) and item.edgeDestination == uri}
        # Use the existing get method to convert URIs to node objects
        incoming_nodes = [self.get(node_uri) for node_uri in incoming_node_uris]
        return [node for node in incoming_nodes if node is not None]  # Filter out any None results

    def get_nodes_outgoing(self, uri: str) -> List[G]:
        """
        Return the node objects that are the destination of an outgoing edge from the given URI.
        """
        outgoing_node_uris = {item.edgeDestination for item in self._data if
                              isinstance(item, VITAL_Edge) and item.edgeSource == uri}
        outgoing_nodes = [self.get(node_uri) for node_uri in outgoing_node_uris]
        return [node for node in outgoing_nodes if node is not None]  # Filter out any None results

    def search(self, query: str, class_uri: str = None, limit: int = 10):

        vs = VitalSigns()

        embedding_model = vs.get_embedding_model(self._embedding_model_id)

        query_embedding = embedding_model.vectorize([query])

        results = self._vectordb.search(query_embedding, class_uri, limit)

        # print(results)

        if results is None:
            return None

        if len(results.get('matches')) == 0:
            return []

        result_list = ResultList()

        count = 0
        for r in results.get('matches'):
            score = results.get('scores')[count]
            uri = r.get('URI')
            obj = self.get(uri)
            re = ResultElement(obj, score)
            result_list.append(re)
            count = count + 1

        return result_list

    def sparql_query(self, sparql_query: str):
        return self._rdfstore.query_graph(sparql_query)

    def to_json(self) -> str:

        obj_list = []

        for obj in self:
            obj_list.append(obj)

        vs = VitalSigns()

        json_string = vs.to_json(obj_list)

        return json_string

    def to_rdf(self) -> str:

        obj_list = []

        for obj in self:
            obj_list.append(obj)

        vs = VitalSigns()

        rdf_string = vs.to_rdf(obj_list)

        return rdf_string


# allow metadata for class for a list of properties to use
# in text when generating vector, with default being "name" property


# to add:
# hypernode and hyperedge cases
