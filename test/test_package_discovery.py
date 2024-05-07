from vital_ai_vitalsigns.vitalsigns import VitalSigns


def main():
    print('Hello World')

    vs = VitalSigns()
    vs.get_registry().build_registry()


if __name__ == "__main__":
    main()
