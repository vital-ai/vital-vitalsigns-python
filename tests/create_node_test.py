from datetime import datetime

from vital_ai_vitalsigns.model.VITAL_Node import VITAL_Node
from vital_ai_vitalsigns_core.model.VitalApp import VitalApp


def main():
    app = VITAL_Node()
    print(app.name)
    app.name = "VitalApp"
    # person.birthday = datetime(1980, 1, 15)
    # person.nothing = "something"
    print(app.name)
    # print(person.birthday.get_uri())
    # print(person.nothing)


if __name__ == "__main__":
    main()
