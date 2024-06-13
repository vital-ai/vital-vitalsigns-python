
class VitalServiceStatus:

    def __init__(self, status: int = 0, message: str = 'Ok'):
        self.status = status
        self.message = message
        self.deleted_objects = 0
        self.inserted_objects = 0
        self.updated_objects = 0
        self.invalid_objects = 0

    def get_status(self):
        return self.status

    def get_message(self):
        return self.message

    def get_changes(self):
        return {
            "inserted_objects": self.inserted_objects,
            "updated_objects": self.updated_objects,
            "deleted_objects": self.deleted_objects,
            "invalid_objects": self.deleted_objects
        }

    def set_changes(self, changes: dict):

        allowed_keys = {"inserted_objects", "updated_objects", "deleted_objects", "invalid_objects"}

        for key, value in changes.items():
            if key in allowed_keys:
                setattr(self, key, value)