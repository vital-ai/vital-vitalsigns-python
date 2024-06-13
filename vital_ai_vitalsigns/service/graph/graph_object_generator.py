
class GraphObjectGenerator:
    def __init__(self, vital_graph_service, graph_uri, class_uri):
        self.vital_graph_service = vital_graph_service
        self.graph_uri = graph_uri
        self.class_uri = class_uri
        self.limit = 100
        self.offset = 0
        self.current_page = []
        self.current_index = 0
        self._fetch_next_page()

    def _fetch_next_page(self):
        # todo use real query function
        self.current_page = self.vital_graph_service.query(
            self.graph_uri, self.class_uri, self.offset, self.limit
        )

        self.offset += self.limit
        self.current_index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.current_index >= len(self.current_page):
            if not self.current_page:
                raise StopIteration
            self._fetch_next_page()
            if not self.current_page:
                raise StopIteration

        obj = self.current_page[self.current_index]
        self.current_index += 1
        return obj

