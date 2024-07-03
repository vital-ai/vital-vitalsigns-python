from typing import TypeVar, Generic, List

T = TypeVar('T')


class UnorderedList(Generic[T]):
    def __init__(self, elements: List[T] = None):
        self.elements = elements if elements else []

    def __repr__(self):
        return f"UnorderedList({self.elements})"

    def __eq__(self, other):
        if not isinstance(other, UnorderedList):
            return NotImplemented
        return sorted(self.elements) == sorted(other.elements)

    def __hash__(self):
        return hash(tuple(sorted(self.elements)))

    def add(self, element: T) -> None:
        self.elements.append(element)

    def remove(self, element: T) -> None:
        self.elements.remove(element)

    def __getitem__(self, index: int) -> T:
        return self.elements[index]

    def __len__(self) -> int:
        return len(self.elements)

    def __iter__(self):
        return iter(self.elements)

    def __contains__(self, item: T) -> bool:
        return item in self.elements

    def to_list(self) -> List[T]:
        return list(self.elements)

