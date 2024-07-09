import os
import sys
from dotenv import load_dotenv, find_dotenv
import logging


def load_env_file():
    current_working_directory = os.getcwd()
    logging.info(f"Current working directory: {current_working_directory}")
    dotenv_path = find_dotenv(filename="vital_env.env", usecwd=True)
    logging.info(f"dotpath: {dotenv_path}")
    if dotenv_path:
        load_dotenv(dotenv_path, override=True)
        logging.info(f"Loaded vital_env.env file from {dotenv_path}")
    else:
        logging.info("vital_env.env file not found")


def find_vitalhome() -> str | None:

    # allow env file to override vital_home
    load_env_file()

    vital_home = os.getenv('VITAL_HOME')

    if not vital_home:
        logging.info("Error: VITAL_HOME environment variable is not set")
        return None

    return vital_home



