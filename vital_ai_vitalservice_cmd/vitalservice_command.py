import argparse
import os
import sys
from vital_ai_vitalsigns.utils.find_vitalhome import find_vitalhome
from vital_ai_vitalsigns.vitalsigns import VitalSigns


class VitalServiceCommand:
    def __init__(self, args):
        self.parser = self.create_parser()
        self.args = self.parser.parse_args()
        # self.vital_home = os.getenv('VITAL_HOME', '')
        self.vital_home = find_vitalhome()

    def create_parser(self):

        parser = argparse.ArgumentParser(prog='vitalservice', description="VitalService Command", add_help=True)

        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        help_parser = subparsers.add_parser('help', help="Display help information")

        status_parser = subparsers.add_parser('status', help="Report general status")

        info_parser = subparsers.add_parser('info', help="Report information about a VitalService")
        info_parser.add_argument('-name', required=True, help="Name of the service")

        list_parser = subparsers.add_parser('list', help="List configured vital services")

        validate_parser = subparsers.add_parser('validate', help="Validate configuration of vital services")
        validate_parser.add_argument('-name', required=False, help="Name of the service")

        init_parser = subparsers.add_parser('initialize', aliases=['init'], help="Initialize a vital service")
        init_parser.add_argument('-name', required=True, help="Name of the service")
        init_parser.add_argument('-vector_schema', required=False, help="Schema in YAML to use for vector database (default to ontology)")

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
        elif self.args.command == 'validate':
            self.validate()
        elif self.args.command == 'initialize' or self.args.command == 'init':
            self.initialize()
        elif self.args.command == 'statistics' or self.args.command == 'stats':
            self.statistics()
        else:
            self.parser.print_help()

    def status(self):
        vital_home = self.vital_home
        print("VitalService Status")
        print(f"Current VITAL_HOME: {vital_home}")
        print("Initializing...")
        vs = VitalSigns()
        print("Initialized.")

    def info(self):
        name = self.args.name
        print(f"VitalService Info: {name}")

    def list(self):
        args = self.args
        print("VitalService List")

    def validate(self):
        name = self.args.name
        if name:
            print(f"VitalService Validate: {name}")
        else:
            print("VitalService Validate")

    def initialize(self):
        name = self.args.name
        print(f"VitalService Initialize: {name}")

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

        print(f"VitalService Statistics: {name}:{db_type}")


def main():
    import sys
    command = VitalServiceCommand(sys.argv[1:])
    command.run()


if __name__ == "__main__":
    main()
