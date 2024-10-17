from typing import TypeVar
from vital_ai_vitalsigns.service.graph.fuseki_service import FusekiService

G = TypeVar('G', bound='GraphObject')


class FusekiMemoryService(FusekiService):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # port, path to java home

    def start(self):
        pass

    def shutdown(self):
        pass

    def import_nquads(self):
        pass

    def export_nquads(self):
        pass


