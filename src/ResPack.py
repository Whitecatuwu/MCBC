from __future__ import annotations
from os import path as os_path, makedirs
from .path_utils import is_valid_pathname, has_matching_part, get_top_dirname
from .Pipe import Pipe
from .Operation import Operation
from loguru import logger
from fnmatch import filter as fn_filter


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
            )
        for key, command in lines.get():
            if command == "":
                continue
            match key:
                case "R":
                    self.__add_rename_oper(output, command)
                case "D":
                    self.__add_delete_oper(output, command)
                case "M":
                    self.__add_modify_oper(output, command)
                case "A":
                    self.__add_apply_oper(output, command)

        self.__process_conflict_oper(output)
        output.build_modify_index()
        output.build_apply_index()
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

    def __add_rename_oper(self, output: Operation, command: str) -> None:
        paths: tuple = (
            Pipe(command)
            .do(lambda x: x.split(",", 1), ...)
            .do(map, lambda x: os_path.normpath(x.strip()), ...)
            .do(map, lambda x: os_path.normcase(x), ...)
            .to(tuple)
            .get()
        )
        if len(paths) < 2:
            logger.warning(f'Rename operation "{command}" require 2 path.')
            return

        src: str = paths[0]
        dst: str = paths[1]

        if not is_valid_pathname(src):
            logger.warning(f"Invalid rename src path: {src}")
            return
        if not is_valid_pathname(dst):
            logger.warning(f"Invalid rename dst path: {dst}")
            return
        if src in output.rename_src:
            logger.warning(
                f"Rename mapping ({src}, {dst}) ignored: ({src}, {output.rename_pair[src]}) already exists."
            )
            return
        if dst in output.rename_dst:
            logger.warning(
                f"Rename mapping ({src}, {dst}) ignored: ({output.rename_inverse_index[dst]}, {dst}) already exists."
            )
            return

        output.add_rename(src, dst)

    def __add_delete_oper(self, output: Operation, command: str) -> None:
        path: str = (
            Pipe(command)
            .do(lambda x: os_path.normpath(x.strip()), ...)
            .do(lambda x: os_path.normcase(x), ...)
            .get()
        )

        if get_top_dirname(path) == "..":
            return
        if path == "" or path == ".":
            return
        output.add_delete(path)

    def __add_modify_oper(self, output: Operation, command: str) -> None:
        paths: tuple = (
            Pipe(command)
            .do(lambda x: x.split(",", 1), ...)
            .do(map, lambda x: os_path.normpath(x.strip()), ...)
            .do(map, lambda x: os_path.normcase(x), ...)
            .to(tuple)
            .get()
        )

        modify_path: str = paths[0]
        subdir: str = paths[1] if len(paths) == 2 else "."

        if not is_valid_pathname(modify_path):
            logger.warning(f"Invalid path: {modify_path}")
            return
        if subdir != "." and not is_valid_pathname(subdir):
            logger.warning(f"Invalid path: {subdir}")
            return

        extract_path = [self.operations_path, subdir, os_path.basename(modify_path)]
        extract_path = os_path.join(*extract_path)
        extract_path = os_path.normpath(extract_path)

        if os_path.exists(extract_path):
            output.modify.add(modify_path)
            output.modify_extract_path[modify_path] = extract_path

    def __add_apply_oper(self, output: Operation, command: str) -> None:
        paths: tuple = (
            Pipe(command)
            .do(lambda x: x.split(",", 1), ...)
            .do(map, lambda x: os_path.normpath(x.strip()), ...)
            .do(map, lambda x: os_path.normcase(x), ...)
            .to(tuple)
            .get()
        )

        apply_path: str = paths[0]
        subdir: str = paths[1] if len(paths) == 2 else "."

        if not is_valid_pathname(apply_path):
            logger.warning(f"Invalid path: {apply_path}")
            return
        if subdir != "." and not is_valid_pathname(subdir):
            logger.warning(f"Invalid path: {subdir}")
            return

        extract_path = [self.operations_path, subdir, os_path.basename(apply_path)]
        extract_path = os_path.join(*extract_path)
        extract_path = os_path.normpath(extract_path)

        if os_path.exists(extract_path):
            output.apply.add(apply_path)
            output.apply_extract_path[apply_path] = extract_path

    def __process_conflict_oper(self, output: Operation) -> None:

        op_set: dict[str, set[str]] = {
            "modify": output.modify,
            "apply": output.apply,
        }
        op_remove: dict[str, callable[[str], None]] = {
            "modify": output.remove_modify,
            "apply": output.remove_apply,
        }
        op_rename_set: dict[str, set[str]] = {
            "src": output.rename_src,
            "dst": output.rename_dst,
        }

        def _rename_pair(path: str, side: str) -> tuple[str, str]:
            if side == "src":
                # assert path in output.rename_pair.keys()
                return path, output.rename_pair[path]
            elif side == "dst":
                # assert path in output.rename_inverse_index.keys()
                return output.rename_inverse_index[path], path
            else:
                raise ValueError()

        def innar(modify_apply: str, rename: str):
            for path in sorted(op_set[modify_apply] & op_rename_set[rename]):
                (src, dst) = _rename_pair(path, rename)
                logger.warning(
                    f"{modify_apply} and rename {rename} conflict: {path} ({src} -> {dst})"
                )
                op_remove[modify_apply](path)
                output.remove_rename(src, dst)

        for ma in ("apply", "modify"):
            for side in ("src", "dst"):
                innar(ma, side)

        # modify and apply conflict is OK.
        # for path in output.apply | output.modify: pass

        candidates = (
            output.apply | output.modify | output.rename_src | output.rename_dst
        )
        delete_targets: set[str] = output.delete.copy()

        for pat in output.delete_pattern:
            delete_targets |= set(fn_filter(candidates, pat))

        for pat in output.delete_pattern_global:
            delete_targets |= {x for x in candidates if has_matching_part(x, pat)}

        modify_conflict: set[str] = output.modify & delete_targets
        apply_conflict: set[str] = output.apply & delete_targets
        rename_src_conflict: set[str] = output.rename_src & delete_targets
        rename_dst_conflict: set[str] = output.rename_dst & delete_targets

        # Deletion has the highest priority.

        # apply and delete conflict
        for path in apply_conflict:
            logger.warning(f"apply and delete conflict: {path}")
            output.remove_apply(path)

        # modify and delete conflict
        for path in modify_conflict:
            logger.warning(f"modify and delete conflict: {path}")
            output.remove_modify(path)

        # rename src and delete conflict
        for path in rename_src_conflict:
            logger.warning(f"rename src and delete conflict: {path}")
            output.remove_rename(path, output.rename_pair[path])

        # rename dst and delete conflict
        for path in rename_dst_conflict:
            logger.warning(f"rename dst and delete conflict: {path}")
            # assert path in output.rename_inverse_index.keys()
            src = output.rename_inverse_index[path]
            output.remove_rename(src, path)
