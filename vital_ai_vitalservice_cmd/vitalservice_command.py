import argparse
import sys
from vital_ai_vitalsigns.utils.find_vitalhome import find_vitalhome
from vital_ai_vitalsigns.vitalsigns import VitalSigns


class VitalServiceCommand:
    def __init__(self, args):
        self.parser = self.create_parser()
        self.args = self.parser.parse_args()
        # self.vital_home = os.getenv('VITAL_HOME', '')
        self.vital_home = find_vitalhome()

    def vs_init(self):
        print("Initializing VitalSigns...")
        vs = VitalSigns()
        print("VitalSigns Initialized.")



    def create_parser(self):

        parser = argparse.ArgumentParser(prog='vitalservice', description="VitalService Command", add_help=True)

        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        help_parser = subparsers.add_parser('help', help="Display help information")

        status_parser = subparsers.add_parser('status', help="Report general status")

        info_parser = subparsers.add_parser('info', help="Report information about a VitalService")
        info_parser.add_argument('-name', required=True, help="Name of the service")

        list_parser = subparsers.add_parser('list', help="List configured vital services")

        list_graph_uris_parser = subparsers.add_parser('list-graph-uris', help="List graph uris in a vital services")
        list_graph_uris_parser.add_argument('-name', required=False, help="Name of the vital service")

        validate_parser = subparsers.add_parser('validate', help="Validate configuration of vital services")
        validate_parser.add_argument('-name', required=False, help="Name of the vital service")

        init_parser = subparsers.add_parser('initialize', aliases=['init'], help="Initialize a vital service")
        init_parser.add_argument('-name', required=True, help="Name of the vital service")
        init_parser.add_argument('-vector_schema', required=False, help="Schema in YAML to use for vector database (default to ontology)")

        destroy_parser = subparsers.add_parser('destroy', help="Destroy a vital service")
        destroy_parser.add_argument('-name', required=True, help="Name of the vital service")

        # add-graph, remove-graph

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
        if self.args.command == 'help':
            self.parser.print_help()
        elif self.args.command == 'status':
            self.status()
        elif self.args.command == 'info':
            self.info()
        elif self.args.command == 'list':
            self.list()
        elif self.args.command == 'list-graph-uris':
            self.list_graph_uris()
        elif self.args.command == 'validate':
            self.validate()
        elif self.args.command == 'initialize' or self.args.command == 'init':
            self.initialize()
        elif self.args.command == 'destroy':
            self.destroy()
        elif self.args.command == 'statistics' or self.args.command == 'stats':
            self.statistics()
        else:
            self.parser.print_help()

    def status(self):
        vital_home = self.vital_home
        print("VitalService Status")
        print(f"Current VITAL_HOME: {vital_home}")
        self.vs_init()
        vs = VitalSigns()
        vitalservice_manager = vs.get_vitalservice_manager()
        service_list = vitalservice_manager.get_vitalservice_list()
        for service in service_list:
            print(f"VitalService: {service}")

    def info(self):
        name = self.args.name
        print(f"VitalService Info.")

        vital_home = self.vital_home
        print(f"Current VITAL_HOME: {vital_home}")
        self.vs_init()
        vs = VitalSigns()

        print(f"VitalService Info: {name}")
        vitalservice_manager = vs.get_vitalservice_manager()
        service_list = vitalservice_manager.get_vitalservice_list()
        if name in service_list:
            print(f"VitalService found in config: {name}")
        else:
            print(f"VitalService not found in config: {name}")



    def list(self):
        args = self.args
        print("VitalService List.")
        vital_home = self.vital_home
        print(f"Current VITAL_HOME: {vital_home}")
        self.vs_init()
        vs = VitalSigns()
        vitalservice_manager = vs.get_vitalservice_manager()
        service_list = vitalservice_manager.get_vitalservice_list()
        for service in service_list:
            print(f"VitalService: {service}")

    def list_graph_uris(self):
        name = self.args.name
        if name:
            print(f"VitalService List Graph URIs.")
            vital_home = self.vital_home
            print(f"Current VITAL_HOME: {vital_home}")
            self.vs_init()
            vs = VitalSigns()
            print(f"VitalService List Graph URIs: {name}")
            vitalservice_manager = vs.get_vitalservice_manager()
            service_list = vitalservice_manager.get_vitalservice_list()
            if name in service_list:
                print(f"VitalService found in config: {name}")

                service = vitalservice_manager.get_vitalservice(name)

                graph_uri_list = service.list_graph_uris()

                for uri in graph_uri_list:
                    print(f"Graph URI: {uri}")
            else:
                print(f"VitalService not found in config: {name}")
        else:
            print("VitalService Validate")


    def validate(self):
        name = self.args.name
        if name:
            print(f"VitalService Validate.")
            vital_home = self.vital_home
            print(f"Current VITAL_HOME: {vital_home}")
            self.vs_init()
            vs = VitalSigns()
            print(f"VitalService Validate: {name}")
            vitalservice_manager = vs.get_vitalservice_manager()
            service_list = vitalservice_manager.get_vitalservice_list()
            if name in service_list:
                print(f"VitalService found in config: {name}")
            else:
                print(f"VitalService not found in config: {name}")
        else:
            print("VitalService Validate")

    def initialize(self):
        name = self.args.name
        print(f"VitalService Initialize.")
        vital_home = self.vital_home
        print(f"Current VITAL_HOME: {vital_home}")
        self.vs_init()
        vs = VitalSigns()
        print(f"VitalService Initialize: {name}")
        vitalservice_manager = vs.get_vitalservice_manager()
        service_list = vitalservice_manager.get_vitalservice_list()
        if name in service_list:
            print(f"VitalService found in config: {name}")
        else:
            print(f"VitalService not found in config: {name}")

    def destroy(self):
        name = self.args.name
        print(f"VitalService Destroy.")

        vital_home = self.vital_home
        print(f"Current VITAL_HOME: {vital_home}")
        self.vs_init()
        vs = VitalSigns()

        print(f"VitalService Destroy: {name}")
        vitalservice_manager = vs.get_vitalservice_manager()
        service_list = vitalservice_manager.get_vitalservice_list()
        if name in service_list:
            print(f"VitalService found in config: {name}")
        else:
            print(f"VitalService not found in config: {name}")


    def statistics(self):
        name = self.args.name
        db_type = self.args.type

        print(f"VitalService Statistics.")

        vital_home = self.vital_home
        print(f"Current VITAL_HOME: {vital_home}")
        self.vs_init()
        vs = VitalSigns()

        vector_db = False
        graph_db = False

        if db_type == "graph":
            graph_db = True

        if db_type == "vector":
            vector_db = True

        if not vector_db and not graph_db:
            print("Type must be 'graph' or 'vector'")
            return

        vitalservice_manager = vs.get_vitalservice_manager()
        service_list = vitalservice_manager.get_vitalservice_list()
        if name in service_list:
            print(f"VitalService found in config: {name}")
        else:
            print(f"VitalService not found in config: {name}")

        print(f"VitalService Statistics: {name}:{db_type}")


def main():
    command = VitalServiceCommand(sys.argv[1:])
    command.run()


if __name__ == "__main__":
    main()
