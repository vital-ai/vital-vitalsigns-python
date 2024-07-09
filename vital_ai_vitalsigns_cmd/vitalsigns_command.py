import argparse
import os
import sys
from vital_ai_vitalsigns.utils.find_vitalhome import find_vitalhome


class VitalSignsCommand:
    def __init__(self, args):
        self.parser = self.create_parser()
        self.args = self.parser.parse_args()

        vital_home = find_vitalhome()

        if vital_home:
            self.vital_home = vital_home
        else:
            self.vital_home = ''

    def create_parser(self):

        parser = argparse.ArgumentParser(prog="vitalsigns", description="VitalSigns Command", add_help=True)
        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        help_parser = subparsers.add_parser('help', help="Display help information")

        info_parser = subparsers.add_parser('info', help="Display information about the system and environment")

        # Generate command
        generate_parser = subparsers.add_parser('generate', help="Generate Ontology Binding")
        generate_parser.add_argument('-o', '--ontology', required=True, help="Ontology file path")

        return parser

    def run(self):
        if self.args.command == 'help':
            self.parser.print_help()
        elif self.args.command == 'info':
            self.info()
        elif self.args.command == 'generate':
            self.generate()
        else:
            self.parser.print_help()

    def generate(self):

        input_path = os.path.join(self.vital_home, self.args.ontology) if not os.path.isabs(
            self.args.ontology) else self.args.ontology

        print(f"Generating files from {input_path}")

    def info(self):
        vital_home = self.vital_home
        print("VitalSigns Info")
        print(f"Current VITAL_HOME: {vital_home}")


def main():
    import sys
    command = VitalSignsCommand(sys.argv[1:])
    command.run()


if __name__ == "__main__":
    main()
