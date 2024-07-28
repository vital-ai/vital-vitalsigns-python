from vital_ai_vitalsigns_generate.vitalsigns_generator import VitalSignsGenerator


def main():
    print('Generate Domain List')

    # location of input, output, path

    input_path = ""

    output_path = ""

    generator = VitalSignsGenerator()

    generator.generate_domain_list()


if __name__ == "__main__":
    main()

