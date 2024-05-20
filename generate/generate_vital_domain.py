from vital_ai_vitalsigns_generate.vitalsigns_generator import VitalSignsGenerator


def main():
    print('Generate Vital Domain')

    # location of input, output, path to core owl ontology

    # vital_core path

    input_path = ""

    output_path = ""

    generator = VitalSignsGenerator()

    generator.generate_vital_domain()


if __name__ == "__main__":
    main()


