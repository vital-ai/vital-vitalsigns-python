from abc import ABC


class PropertyTrait(ABC):
    namespace = "undef#"
    local_name = "undef"

    @classmethod
    def get_uri(cls) -> str:
        """Returns the full URI combining namespace and local name."""
        return f"{cls.namespace}{cls.local_name}"

    @classmethod
    def get_short_name(cls) -> str:
        """Transforms the local name into a short name by removing prefixes and lowercasing the initial letter."""
        name = cls.local_name
        if name.startswith("has"):
            name = name[3:]
        elif name.startswith("is"):
            name = name[2:]

        # Lowercase the first letter and return
        return name[0].lower() + name[1:] if name else name
