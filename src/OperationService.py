from .Operation import Operation
from .tools.Pipe import Pipe
from os import path as os_path
from .tools.path_utils import is_valid_pathname, get_top_dirname, has_matching_part
from fnmatch import filter as fn_filter
from typing import Callable


class OperationService:
    def __init__(
        self,
        docs: str,
        root_path: str,
        operations_path: str,
        exists: Callable[[str], bool],
    ) -> None:
        self.root_path: str = root_path
        self.operations_path: str = operations_path
        self.docs: str = docs
        self.warning_msg: list[str] = []
        self.exists: Callable[[str], bool] = exists

    def run(self) -> tuple[Operation, list[str]]:
        output: Operation = Operation()
        for key, command in self.__parse(self.docs):
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

        return output, self.warning_msg

    def __parse(self, docs) -> list[tuple[str, str]]:
        KEYS: set[str] = {"R", "M", "D", "A"}

        lines = filter(lambda x: not x.startswith("#"), docs)
        lines = map(lambda x: x.strip().split(":", 1), lines)
        lines = filter(lambda x: x[0] in KEYS, lines)

        return list(lines)

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
            self.warning_msg.append(f'Rename operation "{command}" require 2 path.')
            return

        src: str = paths[0]
        dst: str = paths[1]

        if not is_valid_pathname(src):
            self.warning_msg.append(f"Invalid rename src path: {src}")
            return
        if not is_valid_pathname(dst):
            self.warning_msg.append(f"Invalid rename dst path: {dst}")
            return
        if src in output.rename_src:
            self.warning_msg.append(
                f"Rename mapping ({src}, {dst}) ignored: ({src}, {output.rename_pair[src]}) already exists."
            )
            return
        if dst in output.rename_dst:
            self.warning_msg.append(
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
            self.warning_msg.append(f"Invalid path: {modify_path}")
            return
        if subdir != "." and not is_valid_pathname(subdir):
            self.warning_msg.append(f"Invalid path: {subdir}")
            return

        extract_path = [self.operations_path, subdir, os_path.basename(modify_path)]
        extract_path = os_path.join(*extract_path)
        extract_path = os_path.normpath(extract_path)

        if self.exists(extract_path):
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
            self.warning_msg.append(f"Invalid path: {apply_path}")
            return
        if subdir != "." and not is_valid_pathname(subdir):
            self.warning_msg.append(f"Invalid path: {subdir}")
            return

        extract_path = [self.operations_path, subdir, os_path.basename(apply_path)]
        extract_path = os_path.join(*extract_path)
        extract_path = os_path.normpath(extract_path)

        if self.exists(extract_path):
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
                self.warning_msg.append(
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
            self.warning_msg.append(f"apply and delete conflict: {path}")
            output.remove_apply(path)

        # modify and delete conflict
        for path in modify_conflict:
            self.warning_msg.append(f"modify and delete conflict: {path}")
            output.remove_modify(path)

        # rename src and delete conflict
        for path in rename_src_conflict:
            self.warning_msg.append(f"rename src and delete conflict: {path}")
            output.remove_rename(path, output.rename_pair[path])

        # rename dst and delete conflict
        for path in rename_dst_conflict:
            self.warning_msg.append(f"rename dst and delete conflict: {path}")
            # assert path in output.rename_inverse_index.keys()
            src = output.rename_inverse_index[path]
            output.remove_rename(src, path)
