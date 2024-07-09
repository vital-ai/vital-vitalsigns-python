from vital_ai_vitalsigns.service.vital_service_status import VitalServiceStatus
from vital_ai_vitalsigns.vitalsigns import VitalSigns

# implementation of vitalservice command options
# given path to a config file which is by default in vitalhome


class ServiceUtils:
    def __init__(self, config_file=None):

        # allow overriding config file
        vs = VitalSigns()

        vitalservice_manager = vs.get_vitalservice_manager()

        if config_file:
            self.config_file = config_file
            vitalservice_manager.set_config(config_file)
        else:
            # use config file associated with vitalhome
            pass

    def list_services(self):

        vs = VitalSigns()

        vitalservice_manager = vs.get_vitalservice_manager()

        service_names = []

        service_keys = vitalservice_manager.get_vitalservice_list()

        for s in service_keys:
            service_names.append(str(s))

        return service_names

    def list_graphs(self, service_name: str):

        vs = VitalSigns()
        vitalservice_manager = vs.get_vitalservice_manager()

        vitalservice = vitalservice_manager.get_vitalservice(service_name)

        graph_list = vitalservice.list_graphs()

        graph_uri_list = []

        for g in graph_list:
            graph_uri_list.append(str(g.graph_uri))

        return graph_uri_list

    def add_graph(self, service_name: str, graph_uri: str):
        pass

    def delete_graph(self, service_name: str, graph_uri: str):
        pass

    def sync_domains(self, service_name: str):
        pass

    def get_status(self, service_name: str) -> VitalServiceStatus:
        pass



