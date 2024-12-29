import argparse
import json
import logging
import sys
from pathlib import Path

from vital_ai_vitalsigns.metaql.metaql_parser import MetaQLParser
from vital_ai_vitalsigns.utils.find_vitalhome import find_vitalhome
from vital_ai_vitalsigns.vitalsigns import VitalSigns


class VitalServiceQueryCommand:
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

        parser = argparse.ArgumentParser(prog='vitalservice_query', description="VitalService Query Command", add_help=True)

        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        help_parser = subparsers.add_parser('help', help="Display help information")

        status_parser = subparsers.add_parser('status', help="Report general status")

        info_parser = subparsers.add_parser('info', help="Report information about a VitalService")
        info_parser.add_argument('-name', required=True, help="Name of the service")

        # Add: offset, limit, output format, output file or stdout

        query_parser = subparsers.add_parser('query', help="Query a VitalService")
        query_parser.add_argument('-name', required=True, help="Name of the service")
        query_parser.add_argument('-file', required=True, help="File containing MetaQL Query in JSON format")

        list_parser = subparsers.add_parser('list', help="List configured vital services")

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
        elif self.args.command == 'query':
            self.query()
        else:
            self.parser.print_help()

    def status(self):
        vital_home = self.vital_home
        print("VitalService Query Status")
        print(f"Current VITAL_HOME: {vital_home}")
        self.vs_init()
        vs = VitalSigns()
        vitalservice_manager = vs.get_vitalservice_manager()
        service_list = vitalservice_manager.get_vitalservice_list()
        for service in service_list:
            print(f"VitalService: {service}")

    def info(self):
        name = self.args.name
        print(f"VitalService Query Info.")

        vital_home = self.vital_home
        print(f"Current VITAL_HOME: {vital_home}")
        self.vs_init()
        vs = VitalSigns()

        print(f"VitalService Query Info: {name}")
        vitalservice_manager = vs.get_vitalservice_manager()
        service_list = vitalservice_manager.get_vitalservice_list()
        if name in service_list:
            print(f"VitalService found in config: {name}")
        else:
            print(f"VitalService not found in config: {name}")

    def list(self):
        args = self.args
        print("VitalService Query List.")
        vital_home = self.vital_home
        print(f"Current VITAL_HOME: {vital_home}")
        self.vs_init()
        vs = VitalSigns()
        vitalservice_manager = vs.get_vitalservice_manager()
        service_list = vitalservice_manager.get_vitalservice_list()
        for service in service_list:
            print(f"VitalService: {service}")


    def query(self):
        name = self.args.name
        file = self.args.file
        print(f"VitalService Query.")

        vital_home = self.vital_home
        print(f"Current VITAL_HOME: {vital_home}")
        self.vs_init()
        vs = VitalSigns()

        print(f"VitalService Query VitalService: {name}")
        vitalservice_manager = vs.get_vitalservice_manager()
        service_list = vitalservice_manager.get_vitalservice_list()
        if name in service_list:
            print(f"VitalService found in config: {name}")
        else:
            print(f"VitalService not found in config: {name}")
            return

        print(f"VitalService Query File: {file}")

        path = Path(file).resolve()

        with open(path, 'r', encoding='utf-8') as file:

            file_content_json = file.read()

            metaql_query_dict = json.loads(file_content_json)

            print(metaql_query_dict)

            metaql_query = MetaQLParser.parse_metaql_dict(metaql_query_dict)

            graph_query_json = json.dumps(metaql_query, indent=4)

            print(graph_query_json)


def main():

    logging.basicConfig(level=logging.INFO)

    command = VitalServiceQueryCommand(sys.argv[1:])
    command.run()


if __name__ == "__main__":
    main()
