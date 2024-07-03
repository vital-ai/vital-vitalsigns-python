from vital_ai_vitalsigns.service.vital_service import VitalService


class VitalServiceManager:
    def __init__(self, config_file=None):
        self.config_file = config_file
        self.initialized = False
        self.vitalservice_config = None
        self.services = {}

    def set_config(self, config_file: str):
        self.config_file = config_file
        self.initialized = False
        self.vitalservice_config = None
        self.services = {}

    def _initialize(self):
        self.initialized = True

    def get_vitalservice_list(self):

        if self.initialized is False:
            self._initialize()

        return self.services.keys()

    def get_vitalservice(self, vitalservice_name: str) -> VitalService:

        if self.initialized is False:
            self._initialize()

        return self.services[vitalservice_name]




