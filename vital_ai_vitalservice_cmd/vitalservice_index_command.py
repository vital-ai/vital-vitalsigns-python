import argparse
import logging
import os
import sys
from vital_ai_vitalsigns.ntriples.ntriples_reader import NTriplesReader
from vital_ai_vitalsigns.service.graph.graph_object_generator import ListGraphObjectGenerator
from vital_ai_vitalsigns.service.vital_service import VitalService
from vital_ai_vitalsigns.vitalsigns import VitalSigns


class VitalServiceIndexCommand:
    def __init__(self, args):
        self.parser = self.create_parser()
        self.args = self.parser.parse_args()
        self.vital_home = os.getenv('VITAL_HOME', '')

    def vs_init(self):
        vital_home = self.vital_home
        print(f"Current VITAL_HOME: {vital_home}")
        print("Initializing VitalSigns...")
        vs = VitalSigns()
        print("VitalSigns Initialized.")

    def get_vitalservice(self, vitalservice_name) -> VitalService | None:
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

        parser = argparse.ArgumentParser(prog="vitalservice_import", description="VitalServiceImport Command", add_help=True)
        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        help_parser = subparsers.add_parser('help', help="Display help information")

        info_parser = subparsers.add_parser('info', help="Display information about the system and environment")

        index_collections_parser = subparsers.add_parser('index-collections', help="(Testing) Index collections")
        index_collections_parser.add_argument('-name', required=True, help="Name of the vital service")
        index_collections_parser.add_argument('-file', required=True, help="Path to the file to index in the collections.")
        index_collections_parser.add_argument('-graph', required=True, help="Graph identifier to associate with the objects.")
        index_collections_parser.add_argument('-account', required=False, help="Account identifier to associate with the objects.")
        index_collections_parser.add_argument('-global', action='store_true', required=False, help="Whether the graph is global.")
        index_collections_parser.add_argument('-tenant', required=False, help="Tenant identifier to use with collection (if not global).")


        index_collections_parser.add_argument('-purge', action='store_true', required=False, help="Purge all collections of data first.")

        purge_collections_parser = subparsers.add_parser('purge-collections', help="Purge collections")
        purge_collections_parser.add_argument('-name', required=True, help="Name of the vital service")
        purge_collections_parser.add_argument('-graph', required=False, help="Limit purge to a specific graph")

        sync_collections_parser = subparsers.add_parser('sync-collections', help="Sync collections with graph data")
        sync_collections_parser.add_argument('-name', required=True, help="Name of the vital service")
        sync_collections_parser.add_argument('-graph', required=False, help="Limit sync to a specific graph")

        sync_collections_parser.add_argument('-purge', action='store_true', required=False, help="Purge collection(s) of data first.")

        return parser

    def run(self):
        if self.args.command == 'help':
            self.parser.print_help()
        elif self.args.command == 'index-collections':
            self.index_collections()
        elif self.args.command == 'purge-collections':
            self.purge_collections()
        elif self.args.command == 'sync-collections':
            self.sync_collections()
        elif self.args.command == 'info':
            self.info()
        else:
            self.parser.print_help()

    def info(self):
        vital_home = self.vital_home
        print("VitalServiceImport Info")
        print(f"Current VITAL_HOME: {vital_home}")

    def index_collections(self):
        vital_home = self.vital_home
        print("VitalServiceIndex Index-Collections")
        print(f"Current VITAL_HOME: {vital_home}")

        current_directory = os.getcwd()
        print(f"The current working directory is: {current_directory}")

        name = self.args.name
        file = self.args.file

        graph_id = self.args.graph
        account_id = self.args.account
        global_graph = getattr(self.args, 'global')
        tenant_id = self.args.tenant


        self.vs_init()

        vs = VitalSigns()

        service = self.get_vitalservice(name)

        if service:

            status = service.get_service_status()

            print(f"VitalService {name} status: {status.get_status()}")
            print(f"File to index: {file}")

            file_path = os.path.join(current_directory, file)

            reader = NTriplesReader(file_path)

            count = 0

            for triples in reader.read():

                # logging.info(f"triples: {triples}")

                graph_object_list = vs.from_triples_list(triples)

                count += len(graph_object_list)

                # for g in graph_object_list:
                #    print(g.to_json())

                formatted = f"{count:,}"

                go_generator = ListGraphObjectGenerator(graph_object_list)

                service.index_graph_batch(graph_id, go_generator,
                                          global_graph=global_graph,
                                          account_id=account_id,
                                          tenant_id=tenant_id)

                print(f"Processed {formatted} graph_objects.")

            print(f"Total number of graph objects: {count}")

        else:
            print(f"VitalService not found in config: {name}")

    def purge_collections(self):
        vital_home = self.vital_home
        print("VitalServiceIndex Purge-Collections")
        print(f"Current VITAL_HOME: {vital_home}")

        current_directory = os.getcwd()
        print(f"The current working directory is: {current_directory}")
        name = self.args.name

        self.vs_init()

        service = self.get_vitalservice(name)

        if service:
            status = service.get_service_status()

            print(f"VitalService {name} status: {status.get_status()}")


        else:
            print(f"VitalService not found in config: {name}")

    def sync_collections(self):
        vital_home = self.vital_home
        print("VitalServiceIndex Purge-Collections")
        print(f"Current VITAL_HOME: {vital_home}")

        current_directory = os.getcwd()
        print(f"The current working directory is: {current_directory}")
        name = self.args.name

        self.vs_init()

        service = self.get_vitalservice(name)

        if service:
            status = service.get_service_status()

            print(f"VitalService {name} status: {status.get_status()}")


        else:
            print(f"VitalService not found in config: {name}")



def main():

    logging.basicConfig(level=logging.INFO)

    command = VitalServiceIndexCommand(sys.argv[1:])
    command.run()


if __name__ == "__main__":
    main()
