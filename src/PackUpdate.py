from __future__ import annotations
from shutil import copytree
from os import path as os_path
from fnmatch import filter as fn_filter, fnmatch
from .tools.file_operation import delete, copyfile, copyfile_ignore_old, mirror_cleanup
from .ResPack import ResPack
from .tools.path_utils import (
    is_parent_dir,
    get_top_dirname,
    is_path_match,
    path_merge,
    path_split,
)
from .Operation import Operation
from loguru import logger
from collections import deque


class PackUpdate:
    def __init__(self, pre_ver: ResPack, ver: ResPack) -> None:

        self.base_pack: ResPack = pre_ver
        self.pack_for_update: ResPack = ver

        self.operations: Operation
        self.root_src: str = self.base_pack.path
        self.root_dst: str = self.pack_for_update.path
        self.mirror: bool = True

        self.rename_oper: deque[tuple[str, str, Operation]] = deque()
        self.mirror_oper: list[tuple[str, str, set[str]]] = []

    def update(self, mirror=True, ignore_old=True) -> None:
        try:
            self.__update(mirror, ignore_old)
        except Exception as e:
            logger.error(f"Pack update failed because: {e}")
        finally:
            self.rename_oper.clear()
            self.mirror_oper.clear()

    def __update(self, mirror=True, ignore_old=True) -> None:
        src: str = self.root_src
        dst: str = self.root_dst
        self.mirror = mirror
        self.operations = self.pack_for_update.get_operations()

        if not os_path.exists(src):
            logger.warning(f'Warning : "{src}" is does not exist.')
            return
        if not os_path.exists(dst):
            logger.warning(f'Warning : "{dst}" is does not exist.')
            return

        self.__copydata(
            path_merge(src, "assets"),
            path_merge(dst, "assets"),
            operations=self.operations,
            root_src=src,
            root_dst=dst,
            ignore_old=ignore_old,
        )

        if self.operations is None:
            return

        # Handle modify operations
        for M in self.operations.modify:
            src_update: str = self.operations.modify_extract_path[M]
            dst_update: str = path_merge(dst, M)
            self.__copydata(
                src_update,
                dst_update,
                operations=None,
            )

        # Handle apply operations
        for A in self.operations.apply:
            src_update: str = self.operations.apply_extract_path[A]
            dst_update: str = path_merge(dst, A)
            self.__copydata(
                src_update,
                dst_update,
                operations=None,
            )

        # Handle delete operations
        for D in self.operations.delete | self.operations.delete_pattern:
            delete(path_merge(dst, D))
        for D in self.operations.delete_pattern_global:
            delete(path_merge(dst, "**", D))

        # Handle rename operations
        while self.rename_oper:
            src, dst, oper = self.rename_oper.popleft()
            self.__copydata(src, dst, operations=oper)
            logger.trace(f"Rename: {src} -> {dst}")

        # Handle mirror operations
        if mirror:
            for curr_src_dir, curr_dst_dir, keep_set in self.mirror_oper:
                mirror_cleanup(curr_src_dir, curr_dst_dir, keep_set)

    def __copydata(
        self,
        src: str,
        dst: str,
        operations: Operation = None,
        root_src: str = None,
        root_dst: str = None,
        ignore_old: bool = True,
    ) -> None:
        if not os_path.exists(src):
            logger.error(f'Update failed: {dst} \nBecause: "{src}" does not exist.\n')
            return
        if os_path.isdir(src):
            root_src = src if root_src is None else root_src
            root_dst = dst if root_dst is None else root_dst
            copytree(
                src,
                dst,
                dirs_exist_ok=True,
                ignore=self.__operations(operations, root_src, root_dst),
                copy_function=copyfile_ignore_old if ignore_old else copyfile,
            )
            return
        elif os_path.isfile(src):
            if ignore_old:
                copyfile_ignore_old(src, dst)
            else:
                copyfile(src, dst)
            return
        else:
            logger.error(
                f'Update failed: {dst} \nBecause: "{src}" is not a directory or a file.\n'
            )

    def __operations(
        self, operations: Operation, root_src: str, root_dst: str
    ) -> callable:
        """
        根據操作集生成忽略規則，用於複製目錄時的過濾。

        Args:
            operations (dict[str, set]): 操作集，包括新增、修改、刪除、重命名。
            root_src (str): 根來源路徑。
            root_dst (str): 根目標路徑。
            mirror (bool): 是否啟用鏡像模式。

        Returns:
            callable: 用於過濾的函數。
        """

        def __ignore(curr_src_dir: str, src_filenames: list) -> set:
            entry_names_set = set(src_filenames)
            rel_dir: str = os_path.relpath(curr_src_dir, root_src)
            rel_dir = "" if rel_dir == "." else rel_dir
            curr_dst_dir: str = path_merge(root_dst, rel_dir)
            curr_dst_dir_exists: bool = os_path.exists(curr_dst_dir)

            if operations is None:
                # 鏡像模式下清理目標目錄中不在源目錄中的文件
                if self.mirror and curr_dst_dir_exists:
                    self.mirror_oper.append((curr_src_dir, curr_dst_dir, set()))
                return set()

            # 保留集:避免文件在鏡像模式下被刪除
            keep_set: set[str] = set()
            # 刪除集:移除不需要的文件
            delete_set: set[str] = set()
            # 修改集:需要更新的文件
            modify_set: set[str] = set()
            # 新增集:需要新增的文件
            add_set: set[str] = set()
            # 忽略集:不需要處理的文件，包含修改集和刪除集的文件
            ignore_set: set[str] = set()

            # 處理刪除集
            for path_D in operations.delete:
                dirname, filename = os_path.split(path_D)
                if fnmatch(rel_dir, dirname):
                    delete_set.add(filename)
            for path_D in operations.delete_pattern:
                dirname, filename = os_path.split(path_D)
                if is_path_match(rel_dir, dirname):
                    delete_set.update(fn_filter(entry_names_set, filename))
            for path_D in operations.delete_pattern_global:
                delete_set.update(fn_filter(entry_names_set, path_D))

            # 處理修改集
            modify_set = operations.modify_index.get(rel_dir, set())
            modify_set &= entry_names_set

            # 處理新增集
            add_set = operations.apply_index.get(rel_dir, set())
            add_set -= entry_names_set

            # 處理重命名操作
            for path_R_src, path_R_dst in operations.rename_pair.items():
                # 會有重命名至上層路徑的可能性
                # 因此在遞迴操作中，目的路徑有可能包含 ".."，也只有遞迴操作中會發生
                rename_src_path = path_merge(root_src, path_R_src)
                rename_dst_path = path_merge(root_dst, path_R_dst)
                re_src_file = os_path.basename(rename_src_path)
                re_dst_file = os_path.basename(rename_dst_path)

                # 來源不存在，則不進行重命名操作
                if not os_path.exists(rename_src_path):
                    continue

                # 保留重命名操作的目的路徑
                if not curr_dst_dir_exists:
                    pass
                elif curr_dst_dir == os_path.dirname(rename_dst_path):
                    keep_set.add(re_dst_file)
                elif is_parent_dir(curr_dst_dir, rename_dst_path):
                    filename: str = get_top_dirname(
                        os_path.relpath(rename_dst_path, curr_dst_dir)
                    )
                    keep_set.add(filename)

                # 來源加入刪除集
                if curr_src_dir == os_path.dirname(rename_src_path):
                    delete_set.add(re_src_file)
                    self.__set_rename_oper(
                        root_src, root_dst, path_R_src, path_R_dst, operations
                    )

            ignore_set |= delete_set | modify_set
            keep_set |= add_set

            # 鏡像模式下清理目標目錄中不在源目錄中的文件
            if self.mirror and curr_dst_dir_exists:
                self.mirror_oper.append((curr_src_dir, curr_dst_dir, keep_set))

            # logger
            for dele in delete_set:
                logger.trace(f"Ignore src: {path_merge(curr_src_dir, dele)}")
            for mod in modify_set:
                logger.trace(f"Skip src: {path_merge(curr_src_dir, mod)}")
            for add in add_set:
                logger.trace(f"Keep: {path_merge(curr_dst_dir, add)}")

            return ignore_set

        return __ignore

    def __set_rename_oper(
        self,
        root_src: str,
        root_dst: str,
        path_R_src: str,
        path_R_dst: str,
        operations: Operation = None,
    ) -> None:
        rename_src_path = path_merge(root_src, path_R_src)
        rename_dst_path = path_merge(root_dst, path_R_dst)

        if operations is None:
            self.rename_oper.append((rename_src_path, rename_dst_path, None))
            return

        # 若為檔案直接處理即可
        if os_path.isfile(rename_src_path):
            self.rename_oper.append((rename_src_path, rename_dst_path, None))
            return

        # 若為目錄，利用遞迴連帶處理需要被進行操作的子目錄/檔案
        oper: Operation = Operation()

        # Rename
        # 會有重命名至上層路徑的可能性，目的路徑有可能包含 ".."
        tmp = set(
            (x, y)
            for (x, y) in operations.rename_pair.items()
            if is_parent_dir(path_R_src, x) and x != path_R_src
            # and is_parent_dir(path_R_dst, y)
        )

        tmp = (
            (rel_src, rel_dst)
            for (rel_src, rel_dst) in map(
                lambda x: (
                    os_path.relpath(path_merge(root_src, x[0]), rename_src_path),
                    os_path.relpath(path_merge(root_dst, x[1]), rename_dst_path),
                ),
                tmp,
            )
        )
        for s, d in tmp:
            # logger.debug(f"{s}, {d}")
            oper.add_rename(s, d)

        # modify
        # modify 為內容不同而命名(路徑)相同
        # 內容不同且命名(路徑)不同視為相異檔案，因此這裡 modify 不做處理

        # apply
        tmp = set(
            x
            for x in operations.apply
            if any(
                is_parent_dir(path_merge(rename_dst_path, y), path_merge(root_dst, x))
                for y in oper.rename_dst
            )
        )
        tmp |= set(
            x
            for x in operations.apply
            if is_parent_dir(rename_dst_path, path_merge(root_dst, x))
        )
        for a in tmp:
            oper.add_apply(
                os_path.relpath(path_merge(root_dst, a), rename_dst_path),
                operations.apply_extract_path[a],
            )

        # delete
        ## delete_pattern_global
        oper.delete_pattern_global = operations.delete_pattern_global.copy()

        ## delete
        for path, root in [(rename_dst_path, root_dst), (rename_src_path, root_src)]:
            tmp = (
                x for x in operations.delete if is_parent_dir(path, path_merge(root, x))
            )
            tmp = map(lambda x: os_path.relpath(path_merge(root, x), path), tmp)
            oper.delete |= set(tmp)

        ## delete_pattern
        for path, root in [(rename_dst_path, root_dst), (rename_src_path, root_src)]:
            path_len = len(path_split(path))
            for dpat in operations.delete_pattern:
                merged_dpat = path_merge(root, dpat)
                if not is_parent_dir(path, merged_dpat):
                    continue
                dpat_parts: tuple = path_split(merged_dpat)

                if "**" not in dpat_parts or dpat_parts.index("**") > path_len:
                    oper.delete_pattern.add(os_path.relpath(merged_dpat, path))
                else:
                    oper.delete_pattern.add(dpat)

        oper.build_modify_index()
        oper.build_apply_index()
        self.rename_oper.append((rename_src_path, rename_dst_path, oper))
