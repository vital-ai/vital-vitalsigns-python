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

    # should only use config file to define vitalservices, but
    # for testing and other in-memory cases would be useful to define dynamically

    # todo confirm name unique, etc.

    def add_vitalservice(self, vitalservice_name: str, vitalservice: VitalService):
        if self.initialized is False:
            self._initialize()

        self.services[vitalservice_name] = vitalservice
        return True

    def remove_vitalservice(self, vitalservice_name: str):

        if self.initialized is False:
            self._initialize()

        del self.services[vitalservice_name]
        return True




