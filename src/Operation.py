from dataclasses import dataclass, field
from os import path as os_path


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
            dir = os_path.dirname(path_A)
            file = os_path.basename(path_A)
            index.setdefault(dir, set()).add(file)
        self.apply_index = index
