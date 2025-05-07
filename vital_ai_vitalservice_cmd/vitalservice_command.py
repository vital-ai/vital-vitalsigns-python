import argparse
import logging
import sys
from vital_ai_vitalsigns.service.vital_service import VitalService
from vital_ai_vitalsigns.utils.find_vitalhome import find_vitalhome
from vital_ai_vitalsigns.vitalsigns import VitalSigns

class VitalServiceCommand:
    def __init__(self, args):
        self.parser = self.create_parser()
        self.args = self.parser.parse_args()
        # self.vital_home = os.getenv('VITAL_HOME', '')
        self.vital_home = find_vitalhome()

    def vs_init(self):
        vital_home = self.vital_home
        print(f"Current VITAL_HOME: {vital_home}")
        print("Initializing VitalSigns...")
        vs = VitalSigns()
        print("VitalSigns Initialized.")

    def get_vitalservice(self, vitalservice_name) -> VitalService:
        vs = VitalSigns()
        vitalservice_manager = vs.get_vitalservice_manager()
        service_list = vitalservice_manager.get_vitalservice_list()
        if vitalservice_name in service_list:
            print(f"VitalService found in config: {vitalservice_name}")

            service = vitalservice_manager.get_vitalservice(vitalservice_name)

            return service

        else:
            print(f"VitalService not found in config: {vitalservice_name}")
            return None

    def create_parser(self):

        parser = argparse.ArgumentParser(prog='vitalservice', description="VitalService Command", add_help=True)

        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        help_parser = subparsers.add_parser('help', help="Display help information")

        status_parser = subparsers.add_parser('status', help="Report general status")

        info_parser = subparsers.add_parser('info', help="Report information about a VitalService")
        info_parser.add_argument('-name', required=True, help="Name of the service")

        list_parser = subparsers.add_parser('list', help="List configured vital services")

        list_graphs_parser = subparsers.add_parser('list-graphs', help="List graphs in vital services")
        list_graphs_parser.add_argument('-name', required=True, help="Name of the vital service")
        list_graphs_parser.add_argument('-account', required=False, help="Account ID to filter the list by.")


        graph_info_parser = subparsers.add_parser('graph-info', help="Info on Graph in vital services")
        graph_info_parser.add_argument('-name', required=True, help="Name of the vital service")
        graph_info_parser.add_argument('-graph', required=True, help="Name of the graph in vital service")
        graph_info_parser.add_argument('-account', required=False, help="Account ID of the graph.")
        graph_info_parser.add_argument('-global', action='store_true', required=False, help="Declare the graph as globally available in vital service")


        add_graph_parser = subparsers.add_parser('add-graph', help="Add graph to vital services")
        add_graph_parser.add_argument('-name', required=True, help="Name of the vital service")
        add_graph_parser.add_argument('-graph', required=True, help="Name of the graph in vital service")
        add_graph_parser.add_argument('-account', required=False, help="Account ID of the graph.")
        add_graph_parser.add_argument('-global', action='store_true', required=False, help="Declare the graph as globally available in vital service")

        remove_graph_parser = subparsers.add_parser('remove-graph', help="Remove graph from vital services")
        remove_graph_parser.add_argument('-name', required=True, help="Name of the vital service")
        remove_graph_parser.add_argument('-graph', required=True, help="Name of the graph in vital service")
        remove_graph_parser.add_argument('-account', required=False, help="Account ID of the graph.")
        remove_graph_parser.add_argument('-global', action='store_true', required=False, help="Declare the graph as globally available in vital service")

        list_graph_uris_parser = subparsers.add_parser('all-graph-uris', help="List all graph uris in a vital service")
        list_graph_uris_parser.add_argument('-name', required=True, help="Name of the vital service")

        list_collections_all_parser = subparsers.add_parser('all-collection-ids',
                                                            help="List all collection ids in vector db of a vital services")
        list_collections_all_parser.add_argument('-name', required=True, help="Name of the vital service")

        list_collections_parser = subparsers.add_parser('list-collections',
                                               help="List all vital defined collections in a vital services")
        list_collections_parser.add_argument('-name', required=True, help="Name of the vital service")

        init_collections_parser = subparsers.add_parser('init-collections',
                                                        help="Initialize all vital defined collections in a vital services")
        init_collections_parser.add_argument('-name', required=True, help="Name of the vital service")

        remove_collections_parser = subparsers.add_parser('remove-collections',
                                                        help="Remove all vital defined collections in a vital services")
        remove_collections_parser.add_argument('-name', required=True, help="Name of the vital service")

        validate_parser = subparsers.add_parser('validate', help="Validate configuration of vital services")
        validate_parser.add_argument('-name', required=False, help="Name of the vital service")

        init_parser = subparsers.add_parser('initialize', aliases=['init'], help="Initialize a vital service")
        init_parser.add_argument('-name', required=True, help="Name of the vital service")
        init_parser.add_argument('-vector_schema', required=False, help="Schema in YAML to use for vector database (default to ontology)")

        destroy_parser = subparsers.add_parser('destroy', help="Destroy a vital service")
        destroy_parser.add_argument('-name', required=True, help="Name of the vital service")


        # in index command:
        # index operates on collections
        # add-index, re-index, remove-index, sync

        # re-index removes all collections and re-indexes everything

        # sync attempts to re-index just what changed based on which
        # graphs have modifications

        # deletes item in index for changed graphs and re-indexes those
        # so unchanged graphs are unaffected

        # sync-index limited to single collection

        stats_parser = subparsers.add_parser('statistics',  aliases=['stats'], help="Provide statistics and details about a vital service component")
        stats_parser.add_argument('-name', required=True, help="Name of the service")
        stats_parser.add_argument('-type', required=True, help="Type of component: graph or vector")

        return parser

    def run(self):

        self.vs_init()

        if self.args.command == 'help':
            self.parser.print_help()
        elif self.args.command == 'status':
            self.status()
        elif self.args.command == 'info':
            self.info()
        elif self.args.command == 'list':
            self.list()
        elif self.args.command == 'list-graphs':
            self.list_graphs()
        elif self.args.command == 'graph-info':
            self.graph_info()
        elif self.args.command == 'add-graph':
            self.add_graph()
        elif self.args.command == 'remove-graph':
            self.remove_graph()
        elif self.args.command == 'all-graph-uris':
            self.list_graph_uris()
        elif self.args.command == 'validate':
            self.validate()
        elif self.args.command == 'initialize' or self.args.command == 'init':
            self.initialize()
        elif self.args.command == 'all-collection-ids':
            self.list_collections_all()
        elif self.args.command == 'list-collections':
            self.list_collections()
        elif self.args.command == 'init-collections':
            self.init_collections()
        elif self.args.command == 'remove-collections':
            self.remove_collections()
        elif self.args.command == 'destroy':
            self.destroy()
        elif self.args.command == 'statistics' or self.args.command == 'stats':
            self.statistics()
        else:
            self.parser.print_help()

    def status(self):
        vs = VitalSigns()
        vitalservice_manager = vs.get_vitalservice_manager()
        service_list = vitalservice_manager.get_vitalservice_list()
        for service in service_list:
            print(f"VitalService: {service}")

    def info(self):
        name = self.args.name
        print(f"VitalService Info: {name}")

        service = self.get_vitalservice(name)

        if service:
            status = service.get_service_status()
            print(f"VitalService {name} status: {status.get_status()}")
        else:
            print(f"VitalService not found in config: {name}")

    def list(self):
        print("VitalService List.")

        vs = VitalSigns()
        vitalservice_manager = vs.get_vitalservice_manager()
        service_list = vitalservice_manager.get_vitalservice_list()
        for service in service_list:
            print(f"VitalService: {service}")

    def list_graphs(self):
        name = self.args.name
        print(f"VitalService List Graphs: {name}")

        account_id = self.args.account

        service = self.get_vitalservice(name)

        include_global = True
        include_private = True

        if service:
            graph_list = service.list_graphs(
                account_id=account_id,
                include_global=include_global,
                include_private=include_private)

            graph_count = len(graph_list)
            print(f"VitalService {name} Graph Count: {graph_count}")

            for graph in graph_list:
                print(f"Graph URI: {graph.get_graph_uri()}")
        else:
            print(f"VitalService not found in config: {name}")

    def graph_info(self):
        name = self.args.name
        graph = self.args.graph

        account_id = self.args.account
        global_graph = getattr(self.args, 'global')

        print(f"VitalService Graph Info: {name} : {graph}")

        service = self.get_vitalservice(name)

        if service:
            graph_name = service.get_graph(graph,
                                           account_id=account_id,
                                           global_graph=global_graph)

            print(f"VitalService {name} Graph Name: {graph_name}")

        else:
            print(f"VitalService not found in config: {name}")

    def add_graph(self):
        name = self.args.name
        graph = self.args.graph
        account_id = self.args.account

        global_graph = getattr(self.args, 'global')

        print(f"VitalService Add Graph: {name} : {graph} Account: {account_id} Global: {global_graph}")

        service = self.get_vitalservice(name)

        if service:
                created = service.create_graph(graph, account_id=account_id, global_graph=global_graph)
                print(f"VitalService {name} Graph Created: {created}")
        else:
            print(f"VitalService not found in config: {name}")

    def remove_graph(self):
        name = self.args.name
        graph = self.args.graph
        account_id = self.args.account


        global_graph = getattr(self.args, 'global')

        print(f"VitalService Remove Graph: {name} : {graph} Account: {account_id} Global: {global_graph}")

        service = self.get_vitalservice(name)

        if service:
            removed = service.delete_graph(graph, account_id=account_id, global_graph=global_graph)
            print(f"VitalService {name} Graph Removed: {removed}")

        else:
            print(f"VitalService not found in config: {name}")

    def list_graph_uris(self):
        name = self.args.name
        print(f"VitalService List Graph URIs: {name}")

        service = self.get_vitalservice(name)

        if service:
            graph_uri_list = service.list_graph_uris()

            for uri in graph_uri_list:
                print(f"Graph URI: {uri}")
        else:
            print(f"VitalService not found in config: {name}")

    def list_collections_all(self):
        name = self.args.name
        print(f"VitalService List Collection Identifiers: {name}")

        service = self.get_vitalservice(name)

        if service:
            collection_list = service.get_vector_collection_identifiers()
            collection_count = len(collection_list)
            print(f"VitalService List Collection Identifier Count: {collection_count}")

            for collection in collection_list:
                print(f"Collection ID: {collection}")
        else:
            print(f"VitalService not found in config: {name}")

    def list_collections(self):
        name = self.args.name

        print(f"VitalService List Collections: {name}")

        service = self.get_vitalservice(name)

        if service:

            graph_list = service.list_graphs()

            for graph in graph_list:
                print(f"Graph URI: {graph.get_graph_uri()}")
        else:
            print(f"VitalService not found in config: {name}")

    def init_collections(self):
        name = self.args.name
        print(f"VitalService Init Collections: {name}")

        service = self.get_vitalservice(name)

        if service:

            service.init_vector_collections()

        else:
            print(f"VitalService not found in config: {name}")

    def remove_collections(self):
        name = self.args.name
        print(f"VitalService Remove Collections: {name}")

        service = self.get_vitalservice(name)

        if service:
            service.remove_vector_collections()

        else:
            print(f"VitalService not found in config: {name}")

    def validate(self):
        name = self.args.name
        print(f"VitalService Validate: {name}")

        service = self.get_vitalservice(name)

        if service:

            graph_list = service.list_graphs()

        else:
            print(f"VitalService not found in config: {name}")

    def initialize(self):
        name = self.args.name
        print(f"VitalService Initialize: {name}")

        service = self.get_vitalservice(name)

        if service:

            status = service.initialize_service()

            print(f"VitalService {name} status: {status.get_status()}")

        else:
            print(f"VitalService not found in config: {name}")

    def destroy(self):
        name = self.args.name
        print(f"VitalService Destroy: {name}")

        service = self.get_vitalservice(name)

        if service:

            status = service.destroy_service()

            print(f"VitalService {name} status: {status.get_status()}")

        else:
            print(f"VitalService not found in config: {name}")

    def statistics(self):
        name = self.args.name
        db_type = self.args.type

        vector_db = False
        graph_db = False

        if db_type == "graph":
            graph_db = True

        if db_type == "vector":
            vector_db = True

        if not vector_db and not graph_db:
            print("Type must be 'graph' or 'vector'")
            return

        service = self.get_vitalservice(name)

        if service:

            print(f"VitalService Statistics: {name}:{db_type}")

        else:
            print(f"VitalService not found in config: {name}")

def main():

    logging.basicConfig(level=logging.INFO)

    command = VitalServiceCommand(sys.argv[1:])
    command.run()


if __name__ == "__main__":
    main()
