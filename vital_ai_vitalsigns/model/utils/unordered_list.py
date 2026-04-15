from typing import TypeVar, Generic, List

T = TypeVar('T')


class UnorderedList(list, Generic[T]):
    def __init__(self, elements: List[T] = None):
        elements = elements if elements else []
        # Initialize list with the elements - self IS the list now
        list.__init__(self, elements)

    def __repr__(self):
        return f"UnorderedList({list(self)})"

    def __eq__(self, other):
        if not isinstance(other, UnorderedList):
            return NotImplemented
        return sorted(self) == sorted(other)

    def __hash__(self):
        return hash(tuple(sorted(self)))

    def add(self, element: T) -> None:
        self.append(element)

    def remove(self, element: T) -> None:
        # Use list's remove method
        list.remove(self, element)
    
    # __getitem__, __len__, __iter__, __contains__ are inherited from list
    # No need to override them

    def to_list(self) -> List[T]:
        return list(self)
    
    @property
    def elements(self):
        """Returns self as a list"""
        return list(self)

