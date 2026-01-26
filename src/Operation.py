from dataclasses import dataclass, field
from os import path as os_path
from .path_utils import path_split, is_valid_pathname


@dataclass
class Operation:
    delete: set[str] = field(default_factory=set)
    modify: set[str] = field(default_factory=set)
    apply: set[str] = field(default_factory=set)
    rename_src: set[str] = field(default_factory=set)
    rename_dst: set[str] = field(default_factory=set)

    delete_pattern_global: set[str] = field(default_factory=set)
    delete_pattern: set[str] = field(default_factory=set)
    rename_pair: dict[str, str] = field(default_factory=dict)
    modify_extract_path: dict[str, str] = field(default_factory=dict)
    apply_extract_path: dict[str, str] = field(default_factory=dict)

    modify_index: dict[str, set[str]] = field(default_factory=dict)
    apply_index: dict[str, set[str]] = field(default_factory=dict)
    rename_inverse_index: dict[str, str] = field(default_factory=dict)

    def build_modify_index(self) -> None:
        index: dict[str, set[str]] = {}

        for path_M in self.modify:
            dir = os_path.dirname(path_M)
            file = os_path.basename(path_M)
            index.setdefault(dir, set()).add(file)
        self.modify_index = index

    def build_apply_index(self) -> None:
        index: dict[str, set[str]] = {}

        for path_A in self.apply:
            parts: list[str] = path_split(path_A)
            for i in range(len(parts)):
                parent = os_path.join(*parts[:i]) if i > 0 else "."
                child = parts[i]
                index.setdefault(parent, set()).add(child)
        self.apply_index = index

    def add_rename(self, src: str, dst: str) -> None:
        self.rename_src.add(src)
        self.rename_dst.add(dst)
        self.rename_pair[src] = dst
        self.rename_inverse_index[dst] = src

    def remove_rename(self, src: str, dst: str) -> None:
        self.rename_src.discard(src)
        self.rename_dst.discard(dst)
        self.rename_pair.pop(src, None)
        self.rename_inverse_index.pop(dst, None)

    def add_modify(self, path: str, extract_path: str) -> None:
        self.modify.add(path)
        self.modify_extract_path[path] = extract_path

    def remove_modify(self, path: str) -> None:
        self.modify.discard(path)
        self.modify_extract_path.pop(path, None)

    def add_apply(self, path: str, extract_path: str) -> None:
        self.apply.add(path)
        self.apply_extract_path[path] = extract_path

    def remove_apply(self, path: str) -> None:
        self.apply.discard(path)
        self.apply_extract_path.pop(path, None)

    def add_delete(self, path: str) -> None:

        if len(path_split(path)) == 1:
            self.delete_pattern_global.add(path)
        elif is_valid_pathname(path):
            self.delete.add(path)
        else:
            self.delete_pattern.add(path)

    def _validate_invariants(self) -> None:
        "for Test"
        assert self.rename_src == set(self.rename_pair.keys())
        assert self.rename_src == set(self.rename_inverse_index.values())
        assert self.rename_dst == set(self.rename_inverse_index.keys())
        assert self.rename_dst == set(self.rename_pair.values())
        for k, v in self.rename_pair.items():
            assert self.rename_inverse_index[v] == k
        for dst, src in self.rename_inverse_index.items():
            assert self.rename_pair[src] == dst


if __name__ == "__main__":
    parent: str = ""
    parent = os_path.join(*[parent, "a"])
    print(parent)
