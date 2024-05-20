from vital_ai_vitalsigns_generate.vitalsigns_generator import VitalSignsGenerator


def main():
    print('Generate Vital Core')

    input_path = ""

    vital_core_path = ""

    generator = VitalSignsGenerator()

    generator.generate_vital_core()


if __name__ == "__main__":
    main()


