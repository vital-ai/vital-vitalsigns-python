
class VitalNameGraph:
    def __init__(self, graph_uri, *,
                 graph_id: str | None = None,
                 account_id: str | None = None,
                 is_global = False):

        self._graph_uri = graph_uri
        self._account_id = account_id
        self._graph_id = graph_id
        self._is_global = is_global

    def get_graph_uri(self):
        return self._graph_uri

    def get_graph_id(self):
        return self._graph_id

    def get_account_id(self):
        return self._account_id

    def is_global(self):
        return self._is_global

    def __repr__(self):
        return f"VitalNameGraph(graph_uri={self._graph_uri}, is_global={self._is_global})"

