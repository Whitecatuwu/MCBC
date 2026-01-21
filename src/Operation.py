from dataclasses import dataclass, field
from os import path as os_path
from .path_utils import path_split


@dataclass
class Operation:
    delete: set[str] = field(default_factory=set)
    rename: set[tuple[str, str]] = field(default_factory=set)
    modify: set[tuple[str, str]] = field(default_factory=set)
    apply: set[tuple[str, str]] = field(default_factory=set)
    modify_index: dict[str, set[str]] = field(default_factory=dict)
    apply_index: dict[str, set[str]] = field(default_factory=dict)

    def build_modify_index(self) -> None:
        index: dict[str, set[str]] = {}

        for path_M, _ in self.modify:
            dir = os_path.dirname(path_M)
            file = os_path.basename(path_M)
            index.setdefault(dir, set()).add(file)
        self.modify_index = index

    def build_apply_index(self) -> None:
        index: dict[str, set[str]] = {}

        for path_A, _ in self.apply:
            parts: list[str] = path_split(path_A)
            for i in range(len(parts)):
                parent = os_path.join(*parts[:i]) if i > 0 else "."
                child = parts[i]
                index.setdefault(parent, set()).add(child)
        self.apply_index = index


if __name__ == "__main__":
    parent: str = ""
    parent = os_path.join(*[parent, "a"])
    print(parent)
