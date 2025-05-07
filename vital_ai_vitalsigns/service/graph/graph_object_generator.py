from typing import List


class GraphObjectGenerator:
    def __init__(self):
        pass

    def __iter__(self):
        return self

    def __next__(self):
        return None


class QueryGraphObjectGenerator(GraphObjectGenerator):
    def __init__(self, vital_graph_service, graph_uri, class_uri):
        super().__init__()
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

class ListGraphObjectGenerator(GraphObjectGenerator):

    def __init__(self, graph_object_list: List, *, page_size=100):
        super().__init__()
        self.graph_object_list = graph_object_list
        self.page_size = page_size
        self.page = 0

    def __iter__(self):
        return self

    def __next__(self):

        self.page += 1
        start_index = (self.page - 1) * self.page_size
        end_index = start_index + self.page_size

        if start_index < len(self.graph_object_list):
            return self.graph_object_list[start_index:end_index]

        raise StopIteration


