from test_scripts import vitalservice
from vital_ai_vitalsigns.vitalsigns import VitalSigns


class VitalserviceDiagnosticsStatusType:
    VITALSERVICE_OK = "VITALSERVICE_OK"

class VitalserviceDiagnotics:
    diagnostics_status: str

class DiagnosticsManager:
    def __init__(self):
        pass

    # find the unique set of data stores across the defined vitalservices
    # for each graph db, there may be an associated vector db
    # for vitalgraph case, it's a combined graph/vector store

    # for each data store, check its contents for consistency with
    # the service graphs defined, in both graph and vector stores (and vitalgraph combined store).

    def inspect_data_stores(self):

        vs = VitalSigns()

        vitalservice_manager = vs.get_vitalservice_manager()

        vitalservice_name_list = vitalservice_manager.get_vitalservice_list()

        for vitalservice_name in vitalservice_name_list:
            vitalservice = vitalservice_manager.get_vitalservice(vitalservice_name)
            print(f"VitalService Name: {vitalservice.get_vitalservice_name()}")


    # given vitalservice name
    # use vitalsigns config to get graph client and vector client
    # get graphs, for each graph look for vitalsegment objects
    # check naming conventions for graph uri "service_graph" and corresponding
    # vitalsegment objects as expected

    # for vector store, list collections
    # check collections against naming convention, find service graph
    # check service graphs for consistency
    # check service graph object for consistency with graph store

    def inspect_vitalservice(self, vitalservice_name):

        vs = VitalSigns()

        vitalservice_manager = vs.get_vitalservice_manager()

        vitalservice_name_list = vitalservice_manager.get_vitalservice_list()

        for vitalservice_name in vitalservice_name_list:
            vitalservice = vitalservice_manager.get_vitalservice(vitalservice_name)
            print(f"VitalService Name: {vitalservice.get_vitalservice_name()}")

        vitalservice = vitalservice_manager.get_vitalservice(vitalservice_name)



