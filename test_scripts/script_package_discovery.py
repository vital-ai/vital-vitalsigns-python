import logging

from vital_ai_vitalsigns.vitalsigns import VitalSigns


def main():

    logging.basicConfig(level=logging.INFO)

    print('Hello World')

    vs = VitalSigns()
    vs.get_registry().build_registry()


if __name__ == "__main__":
    main()
