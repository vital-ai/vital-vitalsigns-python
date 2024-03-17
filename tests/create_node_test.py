from datetime import datetime

from vital_ai_vitalsigns.model.VITAL_Node import VITAL_Node
from vital_ai_vitalsigns_core.model.VitalApp import VitalApp
from vital_ai_vitalsigns_core.model.VitalServiceSqlConfig import VitalServiceSqlConfig


def main():
    # app = VitalApp()
    app = VitalServiceSqlConfig()
    app.URI = 'urn:123'
    print(app.URI)
    print(app.name)
    app.name = "VitalApp"
    app.username = "Fred"
    # person.birthday = datetime(1980, 1, 15)
    # person.nothing = "something"
    print(app.name)
    print(app.username)
    # print(person.birthday.get_uri())
    # print(person.nothing)


if __name__ == "__main__":
    main()
