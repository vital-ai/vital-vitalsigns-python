from abc import ABC
from functools import lru_cache

class PropertyTrait(ABC):
    namespace = "undef#"
    local_name = "undef"
    multiple_values = False

    @classmethod
    @lru_cache(maxsize=None)
    def get_uri(cls) -> str:
        """Returns the full URI combining namespace and local name."""
        return f"{cls.namespace}{cls.local_name}"

    @classmethod
    @lru_cache(maxsize=None)
    def get_short_name(cls) -> str:
        """Transforms the local name into a short name by removing prefixes and lowercasing the initial letter."""
        name = cls.local_name
        if name.startswith("has"):
            name = name[3:]
        elif name.startswith("is"):
            name = name[2:]

        # Lowercase the first letter and return
        return name[0].lower() + name[1:] if name else name

    @classmethod
    @lru_cache(maxsize=None)
    def get_multiple_values(cls) -> bool:
        """Returns whether this trait may contain multiple values."""
        return cls.multiple_values
