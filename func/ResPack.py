from os import path as os_path, makedirs
from .path_utils import is_valid_pathname
from .gui.ansi import Yellow
from .Pipe import Pipe


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

    def get_operations(self) -> dict[str, set]:
        # R:rename, #M:modify, D:delete, A:add
        if self.operations_path is None:
            return None

        if not os_path.exists(
            docs := os_path.join(self.operations_path, self.DOCS_NAME)
        ):
            self.__write_operations(docs)
            return None

        output: dict[str, set] = {
            "R": set(),
            "M": set(),
            "D": set(),
            "A": set(),
        }
        with open(docs, "r") as r:
            lines = (
                Pipe(r.readlines())
                .do(filter, lambda x: not x.startswith("#"), ...)
                .do(map, lambda x: x.strip().replace("/", "\\").split(":", 1), ...)
                .do(filter, lambda x: x[0] in output.keys(), ...)
                .to(list)
            )
        for key, paths in lines.get():
            paths: list = paths.split(",")
            if len(paths) < 2:
                paths.append("")
            if key == "R" and any(map(lambda x: not is_valid_pathname(x), paths)):
                print(Yellow(f"Warning: Invalid path(s): {paths}"))
                continue
            if key in ("M", "A") and not is_valid_pathname(paths[0]):
                print(Yellow(f"Warning: Invalid path(s): {paths[0]}"))
                continue

            elem = (
                Pipe(paths)
                .do(map, lambda x: os_path.normpath(x.strip().strip("\\")), ...)
                .to(tuple)
                .get()
            )

            match key:
                case "D" | "R":
                    output[key].add(elem)
                case "M" | "A":
                    # elem : [file_name, sub_dir]
                    # Check if path exist : "operations_path/sub_dir/file_name"
                    # or "operations_path/file_name" if sub_dir is empty
                    temp = filter(
                        lambda x: x != ".",
                        [self.operations_path, elem[1], os_path.basename(elem[0])],
                    )
                    if os_path.exists(os_path.join(*temp)):
                        output[key].add(elem)
        return output

    def __write_operations(self, docs) -> None:
        WARNING_MSG: str = (
            f"Warning: {self.DOCS_NAME} in {self.operations_path} does not exist, it will be created."
        )
        print(Yellow(WARNING_MSG))

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
