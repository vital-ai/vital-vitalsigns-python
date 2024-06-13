import yaml


class ConfigUtils:

    @staticmethod
    def load_config():
        with open("../config/vitalsigns_config.yaml", "r") as config_stream:
            try:
                return yaml.safe_load(config_stream)
            except yaml.YAMLError as exc:
                print("failed to load config file")
