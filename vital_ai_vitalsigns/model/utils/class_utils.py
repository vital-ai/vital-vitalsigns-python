
class ClassUtils:

    @classmethod
    def get_class_hierarchy(cls, clz, top_level_class):

        hierarchy: list[type] = []

        current_class = clz

        while current_class is not top_level_class:
            hierarchy.append(current_class)
            current_class = current_class.__bases__[0]
            if current_class is object:
                break

        hierarchy.append(top_level_class)

        return hierarchy
