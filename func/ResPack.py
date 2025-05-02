from os import path as os_path, makedirs
from .pathutils import is_valid_pathname
from .ansi import Yellow

RESOURCE_VER = {
    "": 0,  # common version
    "1.8.9": 1,
    "1.10.2": 2,
    "1.12.2": 3,
    "1.14.4": 4,
    "1.16.1": 5,
    "1.16.5": 6,
    "1.17.1": 7,
    "1.18.2": 8,
    "1.19.2": 9,
    "1.19.3": 12,
    "1.19.4": 13,
    "1.20.1": 15,
    "1.20.2": 18,
    "1.20.4": 22,
    "1.20.6": 32,
    "1.21.1": 34,
    "1.21.3": 39,
    "1.21.4": 46,
    "1.21.5": 55,
}


class ResPack:

    def __init__(self, path: str, ver: str, operations_path: str = None):
        self.DOCS_NAME: str = "operations.txt"
        self.path: str = None
        self.ver: str = None
        self.ver_num: int = None
        self.operations_path: str = None
        self.operations_list: dict[str, list] = None

        self.__set_path(path)
        self.__set_operations_path(operations_path)
        self.__set_ver(ver)

    def version(self) -> str:
        return self.ver

    def version_num(self) -> int:
        return self.ver_num

    def get_operations(self) -> dict[str, list]:
        # R:rename, #M:modify, D:delete, A:add
        if self.operations_list is not None:
            return self.operations_list

        if self.operations_path is None:
            return None

        if not os_path.exists(
            docs := os_path.join(self.operations_path, self.DOCS_NAME)
        ):
            self.__write_operations(docs)
            return None

        output: dict[str, list] = {"R": [], "M": [], "D": [], "A": []}
        with open(docs, "r") as r:
            key: str
            paths: str
            for i in r.readlines():
                if i.startswith("#"):
                    continue
                i = i.strip().replace("/", "\\").split(":", 1)
                if (key := i[0]) not in output.keys():
                    continue
                paths = i[1].split(",")
                if key in ("A", "R", "M") and not all(map(is_valid_pathname, paths)):
                    print(Yellow(f'Warning : "{paths}" is not a valid path name.'))
                    continue
                output[key].append(
                    tuple(map(lambda x: os_path.normpath(x.strip("\\")), paths))
                )
        self.operations_list = output
        return output

    def __write_operations(self, docs) -> None:
        print(
            Yellow(
                f"Warning: {self.DOCS_NAME} in {self.operations_path} does not exist, it will be created."
            )
        )

        if not os_path.exists(os_path.dirname(docs)):
            makedirs(os_path.dirname(docs))
        with open(docs, "w") as w:
            w.write("# Specify the relative paths to resource pack contents.\n")
            w.write("# Each line starts with a prefix indicating the action:\n")
            w.write(
                "#   R: Rename   (e.g., R:assets/minecraft/textures/item,assets/minecraft/item)\n"
            )
            w.write("#   M: Modify   (e.g., M:assets/minecraft/textures/item)\n")
            w.write("#   D: Delete   (e.g., D:assets/minecraft/textures/item)\n")
            w.write("#   A: Add      (e.g., A:assets/minecraft/textures/item)\n")
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
        p = os_path.normpath(os_path.abspath(path))
        if os_path.exists(p):
            self.path = p
        else:
            raise ValueError(f"Invalid path: {path}")

    def __set_ver(self, ver: str) -> None:
        if ver in RESOURCE_VER:
            self.ver = ver
            self.ver_num = RESOURCE_VER[ver]
        else:
            raise ValueError(f"Invalid version: {ver}")

    def __set_operations_path(self, path: str = None) -> None:
        if path is None:
            return
        p = os_path.normpath(os_path.abspath(path))
        if os_path.exists(p):
            self.operations_path = p
        else:
            raise ValueError(f"Invalid path: {path}")
