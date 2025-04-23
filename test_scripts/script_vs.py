from vital_ai_vitalsigns.vitalsigns import VitalSigns

def main():

    print('Hello World')

    vs = VitalSigns()

    print("VitalSigns Initialized")

    vital_home = vs.get_vitalhome()

    print(f"VitalSigns Home: {vital_home}")

if __name__ == "__main__":
    main()
