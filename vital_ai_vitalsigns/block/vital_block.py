from vital_ai_vitalsigns.model.GraphObject import GraphObject


class VitalBlock:
    def __init__(self, objects):
        if not objects:
            raise ValueError("A block cannot be empty")

        if self._is_graphobject_list(objects):
            self.objects = objects
            return

        self.objects = [GraphObject.from_json(obj) for obj in objects]

    @property
    def first_object(self):
        return self.objects[0]

    @property
    def rest_objects(self):
        return self.objects[1:] if len(self.objects) > 1 else []

    def __repr__(self):
        return f"VitalBlock(first_object={self.first_object}, rest_objects={len(self.rest_objects)})"

    def _is_graphobject_list(self, objects) -> bool:

        if not isinstance(objects, list):
            return False

        if len(objects) == 0:
            return False

        is_graphobject_list = True

        for g in objects:
            if not isinstance(g, GraphObject):
                return False

        return is_graphobject_list
