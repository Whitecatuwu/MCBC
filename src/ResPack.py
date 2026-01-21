from __future__ import annotations
from os import path as os_path, makedirs
from .path_utils import is_valid_pathname
from .Pipe import Pipe
from .Operation import Operation
from loguru import logger


class ResPack:

    def __init__(self, path: str, ver: str, operations_path: str = None):
        self.DOCS_NAME: str = "operations.txt"
        self.path: str = None
        self.ver: str = ver
        self.operations_path: str = None

        self.__set_path(path)
        self.__set_operations_path(operations_path)

    def version(self) -> str:
        return self.ver

    def get_operations(self) -> Operation:
        KEYS: set[str] = {"R", "M", "D", "A"}
        if self.operations_path is None:
            return None

        if not os_path.exists(
            docs := os_path.join(self.operations_path, self.DOCS_NAME)
        ):
            self.__write_operations(docs)
            return None

        output: Operation = Operation()
        with open(docs, "r") as r:
            lines = (
                Pipe(r.readlines())
                .do(filter, lambda x: not x.startswith("#"), ...)
                .do(map, lambda x: x.strip().split(":", 1), ...)
                .do(filter, lambda x: x[0] in KEYS, ...)
                .to(list)
            )
        for key, paths in lines.get():
            paths: tuple[str, str] = paths.split(",")
            if key == "R" and any(map(lambda x: not is_valid_pathname(x), paths)):
                logger.warning(f"Invalid path(s): {paths}")
                continue
            if key in ("M", "A") and not is_valid_pathname(paths[0]):
                logger.warning(f"Invalid path(s): {paths[0]}")
                continue

            elem: tuple = (
                Pipe(paths)
                .do(map, lambda x: os_path.normpath(x.strip().strip("\\")), ...)
                .to(tuple)
                .get()
            )

            match key:
                case "R":
                    output.rename.add(elem)
                case "D":
                    output.delete.add(elem[0])
                # elem : [file_name, sub_dir]
                # Check if path exist : "operations_path/sub_dir/file_name"
                # or "operations_path/file_name" if sub_dir is empty
                case "M":
                    has_subdir: bool = len(elem) == 2 and elem[1] != "."
                    temp = (
                        [self.operations_path, elem[1], os_path.basename(elem[0])]
                        if has_subdir
                        else [self.operations_path, os_path.basename(elem[0])]
                    )
                    if os_path.exists(os_path.join(*temp)):
                        output.modify.add(elem if has_subdir else (elem[0], None))
                case "A":
                    has_subdir: bool = len(elem) == 2 and elem[1] != "."
                    temp = (
                        [self.operations_path, elem[1], os_path.basename(elem[0])]
                        if has_subdir
                        else [self.operations_path, os_path.basename(elem[0])]
                    )
                    if os_path.exists(os_path.join(*temp)):
                        output.apply.add(elem if has_subdir else (elem[0], None))
        return output

    def __write_operations(self, docs) -> None:
        logger.info(
            f"{self.DOCS_NAME} in {self.operations_path} does not exist, it will be created."
        )

        if not os_path.exists(os_path.dirname(docs)):
            makedirs(os_path.dirname(docs))
        with open(docs, "w") as w:
            w.write("# Specify the relative paths to resource pack contents.\n")
            w.write("# Each line starts with a prefix indicating the action:\n")
            w.write("#   R: Rename <old path>,<new path>\n")
            w.write(
                "#   e.g. R:assets/minecraft/textures/item,assets/minecraft/item\n\n"
            )
            w.write("#   M: Modify <path>,[sub_dir]\n")
            w.write("#   e.g. M:assets/minecraft/textures/item\n\n")
            w.write("#   A: Add <path>,[sub_dir]\n")
            w.write("#   e.g. A:assets/minecraft/textures/item\n\n")
            w.write("#   D: Delete <path (allow shell patterns)> \n")
            w.write("#   e.g. D:assets/minecraft/textures/item\n")
            w.write(
                "#   D:*unused (Deletes all files/directories ending with 'unused')\n"
            )
            w.write(
                "#   D:assets/*unused (Deletes files/directories ending with 'unused' only in the 'assets' folder)\n"
            )
            w.write("#\n")
            w.write(
                "# All paths must be *relative* to the root of the resource pack.\n"
            )
            w.write("# Do NOT provide full system paths like this:\n")
            w.write(
                "#   home/user/projects/my_resource_pack/assets/minecraft/textures/item\n"
            )
            w.write("# Instead, start from inside the resource pack, like:\n")
            w.write("#   assets/minecraft/textures/item\n")

    def __set_path(self, path: str) -> None:
        # p = os_path.normpath(os_path.abspath(path))
        p = Pipe(path).to(os_path.abspath).to(os_path.normpath).get()
        if os_path.exists(p):
            self.path = p
        else:
            raise ValueError(f"Invalid path: {p}")

    def __set_operations_path(self, path: str = None) -> None:
        if path is None:
            return
        # p = os_path.normpath(os_path.abspath(path))
        p = Pipe(path).to(os_path.abspath).to(os_path.normpath).get()
        if os_path.exists(p):
            self.operations_path = p
        else:
            raise ValueError(f"Invalid path: {p}")
