import argparse
import os
import time

import paramiko
from paramiko.client import SSHClient
from scp import SCPClient

from vital_ai_vitalsigns.service.graph.virtuoso.virtuoso_service import VirtuosoGraphService
from vital_ai_vitalsigns.vitalsigns import VitalSigns


class VitalServiceImportCommand:
    def __init__(self, args):
        self.parser = self.create_parser()
        self.args = self.parser.parse_args()
        self.vital_home = os.getenv('VITAL_HOME', '')

    def vs_init(self):
        print("Initializing VitalSigns...")
        vs = VitalSigns()
        print("VitalSigns Initialized.")

    def upload_file_scp(self, hostname, username, pem_file, local_path, remote_path) -> bool:
        ssh_client = SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh_client.connect(hostname, username=username, key_filename=pem_file)
            sftp = ssh_client.open_sftp()

            # Check if the file exists
            try:
                sftp.stat(remote_path)
                print(f"File already exists at {remote_path}.")
                # return False
            except FileNotFoundError:
                pass  # File does not exist, proceed with upload

            with SCPClient(ssh_client.get_transport()) as scp:
                scp.put(local_path, remote_path)
                print(f"File uploaded successfully to {remote_path}")
                return True

        except Exception as e:
            return False
        finally:
            ssh_client.close()

    def create_parser(self):

        parser = argparse.ArgumentParser(prog="vitalservice_import", description="VitalServiceImport Command", add_help=True)
        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        help_parser = subparsers.add_parser('help', help="Display help information")

        info_parser = subparsers.add_parser('info', help="Display information about the system and environment")

        import_parser = subparsers.add_parser('import', help="Display information about the system and environment")
        import_parser.add_argument('-name', required=True, help="Name of the vital service")
        import_parser.add_argument('-graph', required=True, help="Graph to import the file into")
        import_parser.add_argument('-file', required=True, help="Path to the file to import into the vital service")

        import_parser.add_argument('-create', action='store_true', required=False, help="Create the graph Graph if it doesn't exist.")
        import_parser.add_argument('-replace', action='store_true', required=False, help="Delete an existing graph if it exists.")

        return parser

    def run(self):
        if self.args.command == 'help':
            self.parser.print_help()
        elif self.args.command == 'import':
            self.import_file()
        elif self.args.command == 'info':
            self.info()
        else:
            self.parser.print_help()

    def info(self):
        vital_home = self.vital_home
        print("VitalServiceImport Info")
        print(f"Current VITAL_HOME: {vital_home}")

    def import_file(self):
        vital_home = self.vital_home
        print("VitalServiceImport Info")
        print(f"Current VITAL_HOME: {vital_home}")

        current_directory = os.getcwd()
        print(f"The current working directory is: {current_directory}")
        name = self.args.name
        graph = self.args.graph
        file = self.args.file

        vital_home = self.vital_home
        print(f"Current VITAL_HOME: {vital_home}")
        self.vs_init()
        vs = VitalSigns()

        print(f"VitalService Info: {name}")
        vitalservice_manager = vs.get_vitalservice_manager()
        service_list = vitalservice_manager.get_vitalservice_list()
        if name in service_list:
            print(f"VitalService found in config: {name}")

            service = vitalservice_manager.get_vitalservice(name)

            status = service.get_service_status()

            print(f"VitalService {name} status: {status.get_status()}")

            graph_service: VirtuosoGraphService = service.graph_service

            server_name = graph_service.server_name
            server_user = graph_service.server_user
            server_dataset_dir = graph_service.server_dataset_dir
            pem_path = graph_service.pem_path

            print(f"Importing into graph {graph}: {file}")

            print(f"Server Name: {server_name}")
            print(f"Server User: {server_user}")

            print(f"PEM Path: {pem_path}")

            print(f"Server Dataset Path: {server_dataset_dir}")

            filename = os.path.basename(file)

            print(f"Filename to upload: {filename}")

            remote_file = f"{server_dataset_dir}/{filename}"

            upload_success = self.upload_file_scp(
                hostname=server_name,
                username=server_user,
                pem_file=pem_path,
                local_path=file,
                remote_path=remote_file
            )

            graph_uri = "http://vital.ai/graph/wordnet-frames-import-graph-1"

            check_interval = 10

            try:
                graph_service.trigger_bulk_import(graph_uri, filename)
            except Exception as e:
                print("Bulk import could not be triggered.")
                return

            while True:
                try:
                    statuses = graph_service.check_import_status_for_file(filename)
                    if not statuses:
                        print("Import status not found. Retrying...")
                    else:
                        for status in statuses:
                            state = status.get("state")
                            load = status.get("load", "Unknown load")

                            if state == 1:
                                print(f"File '{filename}' is currently loading (Load ID: {load}).")
                            elif state == 2:
                                print(f"File '{filename}' has been successfully loaded (Load ID: {load}).")
                                break
                            elif state == 3:
                                error_message = status.get("error", "No error details available.")
                                print(f"File '{filename}' encountered an error: {error_message} (Load ID: {load}).")
                                break
                            else:
                                print(f"Unknown state ({state}) for file '{filename}' (Load ID: {load}).")
                        else:
                            # Continue checking if no final states (2 or 3) are found
                            time.sleep(check_interval)
                            continue
                            # Exit the loop when a final state is found
                        break
                except Exception as e:
                    print(f"Error monitoring status: {e}")
                    break


        else:
            print(f"VitalService not found in config: {name}")


def main():
    import sys
    command = VitalServiceImportCommand(sys.argv[1:])
    command.run()


if __name__ == "__main__":
    main()
