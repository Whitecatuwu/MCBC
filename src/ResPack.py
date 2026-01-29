from __future__ import annotations
from os import path as os_path, makedirs
from .tools.path_utils import (
    path_merge,
)
from .Operation import Operation
from .OperationBuilder import OperationBuilder
from loguru import logger


class ResPack:

    def __init__(self, path: str, ver: str, operations_path: str = None):
        self.DOCS_NAME: str = "operations.txt"
        self.ver: str = ver
        self.path: str = self.__set_path(path)
        self.operations_path: str = self.__set_operation_path(operations_path)
        self.docs_path: str = self.__set_docs_path(self.operations_path, self.DOCS_NAME)

    def version(self) -> str:
        return self.ver

    def get_operation(self) -> Operation:
        if self.docs_path is None:
            return None

        if not os_path.exists(self.docs_path):
            self.__write_operations(self.docs_path)
            return None

        with open(self.docs_path, "r") as r:
            docs = r.readlines()

        oper_service = OperationBuilder(
            docs, self.path, self.operations_path, os_path.exists
        )
        output, warning_msg = oper_service.build()

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

    def __set_path(self, path: str) -> str:
        p = os_path.normpath(path)
        if os_path.exists(p):
            return p
        else:
            raise ValueError(f"Invalid path: {p}")

    def __set_operation_path(self, path: str = None) -> str:
        if path is None:
            return None
        p = os_path.normpath(path)
        if os_path.exists(p):
            return p
        else:
            raise ValueError(f"Invalid path: {p}")

    def __set_docs_path(self, path: str, name: str) -> str:
        if path is None or name is None:
            return None
        return path_merge(path, name)
