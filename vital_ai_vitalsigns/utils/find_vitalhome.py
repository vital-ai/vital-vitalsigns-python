import os
import sys
from dotenv import load_dotenv, find_dotenv
import logging


def load_env_file():

    # print(f"os path: {os.path.abspath(__file__)}")

    file_directory = os.path.dirname(os.path.abspath(__file__))

    dotenv_path = find_dotenv_in_path(file_directory, "vital_env.env")
    logging.info(f"testing dotpath: {dotenv_path}")
    if dotenv_path:
        load_dotenv(dotenv_path, override=True)
        logging.info(f"Loaded vital_env.env file from {dotenv_path}")

        relative_vital_home = os.environ.get('RELATIVE_VITAL_HOME')

        if relative_vital_home:
            vh_parent = os.path.dirname(dotenv_path)
            vh_path = os.path.join(vh_parent, relative_vital_home)
            os.environ['VITAL_HOME'] = vh_path
        return

    current_working_directory = os.getcwd()
    logging.info(f"Current working directory: {current_working_directory}")
    dotenv_path = find_dotenv(filename="vital_env.env", usecwd=True)
    logging.info(f"testing dotpath: {dotenv_path}")
    if dotenv_path:
        load_dotenv(dotenv_path, override=True)
        logging.info(f"Loaded vital_env.env file from {dotenv_path}")

        relative_vital_home = os.environ.get('RELATIVE_VITAL_HOME')

        if relative_vital_home:
            vh_parent = os.path.dirname(dotenv_path)
            vh_path = os.path.join(vh_parent, relative_vital_home)
            os.environ['VITAL_HOME'] = vh_path

    else:
        logging.info("vital_env.env file not found")


def find_dotenv_in_path(start_path, filename="vital_env.env"):

    current_path = os.path.abspath(start_path)

    # print(current_path)

    while True:
        potential_path = os.path.join(current_path, filename)
        if os.path.isfile(potential_path):
            return potential_path

        # Move to the parent directory
        parent_path = os.path.dirname(current_path)

        # If the current path and the parent path are the same, we have reached the root
        if current_path == parent_path:
            break

        current_path = parent_path

    return None


def find_vitalhome() -> str | None:

    # allow env file to override vital_home
    load_env_file()

    vital_home = os.getenv('VITAL_HOME')

    if not vital_home:
        logging.info("Error: VITAL_HOME environment variable is not set")
        return None

    return vital_home



