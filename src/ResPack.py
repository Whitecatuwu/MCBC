from __future__ import annotations
from os import path as os_path, makedirs
from .tools.path_utils import (
    path_merge,
)
from .Operation import Operation
from .OperationService import OperationService
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
        if self.operations_path is None:
            return None

        docs_path: str = path_merge(self.operations_path, self.DOCS_NAME)
        if not os_path.exists(docs_path):
            self.__write_operations(docs_path)
            return None

        with open(docs_path, "r") as r:
            docs = r.readlines()

        oper_service = OperationService(
            docs, self.path, self.operations_path, os_path.exists
        )
        output, warning_msg = oper_service.run()

        for msg in warning_msg:
            logger.warning(msg)

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
        p = os_path.normpath(path)
        if os_path.exists(p):
            self.path = p
        else:
            raise ValueError(f"Invalid path: {p}")

    def __set_operations_path(self, path: str = None) -> None:
        if path is None:
            return
        p = os_path.normpath(path)
        if os_path.exists(p):
            self.operations_path = p
        else:
            raise ValueError(f"Invalid path: {p}")
