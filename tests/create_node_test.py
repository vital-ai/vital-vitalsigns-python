from datetime import datetime

from vital_ai_vitalsigns_core.model.Person import Person


def main():
    person = Person()
    print(person.name)
    person.name = "John"
    person.birthday = datetime(1980, 1, 15)
    # person.nothing = "something"
    print(person.name)
    print(person.birthday)
    # print(person.nothing)


if __name__ == "__main__":
    main()
