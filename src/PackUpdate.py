from __future__ import annotations
from shutil import copytree
from os import path as os_path
from fnmatch import filter as fn_filter
from .file_operation import delete, copyfile, copyfile_ignore_old, mirror_cleanup
from .ResPack import ResPack
from .path_utils import is_parent_dir, get_top_dirname
from .Pipe import Pipe
from .Operation import Operation
from loguru import logger
from collections import deque


class PackUpdate:
    def __init__(self, pre_ver: ResPack, ver: ResPack) -> None:
        self.pre_ver: ResPack = pre_ver
        self.ver: ResPack = ver
        self.operations: Operation = self.ver.get_operations()
        self.root_src: str = self.pre_ver.path
        self.root_dst: str = self.ver.path

        self.rename_oper: deque[tuple[str, str, Operation]] = deque()
        self.delete_path: set[str] = set()
        self.mirror_oper: list[tuple[str, str, set[str]]] = []

    def update(self, mirror=True, ignore_old=True) -> None:
        src: str = self.root_src
        dst: str = self.root_dst

        if not os_path.exists(src):
            logger.warning(f'Warning : "{src}" is does not exist.')
            return
        if not os_path.exists(dst):
            logger.warning(f'Warning : "{dst}" is does not exist.')
            return

        self.copydata(
            os_path.join(src, "assets"),
            os_path.join(dst, "assets"),
            operations=self.operations,
            root_src=src,
            root_dst=dst,
            mirror=mirror,
            ignore_old=ignore_old,
        )

        if self.operations is None:
            return

        # Handle modify, apply operations
        for MA, sub_dir in self.operations.modify | self.operations.apply:
            temp = filter(
                lambda x: x is not None,
                [self.ver.operations_path, sub_dir, os_path.basename(MA)],
            )
            src_update: str = os_path.join(*temp)
            dst_update: str = os_path.join(dst, MA)
            self.copydata(
                src_update,
                dst_update,
                operations=None,
                mirror=mirror,
            )

        # Handle delete operations
        for D in self.operations.delete:
            if os_path.split(D)[0] == "":
                delete(os_path.join(dst, "**", D))
            else:
                delete(os_path.join(dst, D))

        # Handle delete paths from rename operations
        for delete_path in self.delete_path:
            delete(delete_path)

        # Handle mirror operations
        for current_dirname, path_dst, keep_set in self.mirror_oper:
            mirror_cleanup(current_dirname, path_dst, keep_set)

        # Handle rename operations
        while self.rename_oper:
            src, dst, oper = self.rename_oper.popleft()
            if oper is None:
                self.copydata(src, dst)
            else:
                self.copydata(src, dst, operations=oper, mirror=mirror)
            logger.trace(f"Rename: {src} -> {dst}")

        self.rename_oper.clear()
        self.delete_path.clear()
        self.mirror_oper.clear()

    def copydata(
        self,
        src: str,
        dst: str,
        operations: Operation = None,
        root_src: str = None,
        root_dst: str = None,
        mirror: bool = False,
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
                ignore=self.__operations(operations, root_src, root_dst, mirror=mirror),
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
        self,
        operations: Operation,
        root_src: str,
        root_dst: str,
        mirror: bool = False,
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

        def __ignore(current_dirname: str, src_filenames: list) -> set:
            entry_names_set = set(src_filenames)
            rel_src_dir: str = os_path.relpath(current_dirname, root_src)

            # 保留集:避免文件在鏡像模式下被刪除
            keep_set: set[str] = entry_names_set
            # 刪除集:移除不需要的文件
            delete_set: set[str] = set()
            # 修改集:需要更新的文件
            modify_set: set[str] = set()
            # 新增集:需要新增的文件
            add_set: set[str] = set()
            # 忽略集:不需要處理的文件，包含修改集和刪除集的文件
            ignore_set: set[str] = set()

            if operations is None:
                pass
            else:
                # 處理刪除集
                for path_D in operations.delete:
                    dirname, filename = os_path.split(os_path.join(root_src, path_D))
                    is_global_ignore: bool = os_path.normpath(
                        dirname
                    ) == os_path.normpath(root_src)
                    if (
                        not fn_filter([current_dirname], dirname)
                        and not is_global_ignore
                    ):
                        continue
                    names_set: set = set(fn_filter(src_filenames, filename))
                    delete_set.update(names_set)

                # 處理修改集
                modify_set = entry_names_set & operations.modify_index.get(
                    rel_src_dir, set()
                )

                # 處理新增集
                add_set = (
                    operations.apply_index.get(rel_src_dir, set()) - entry_names_set
                )

                # 處理重命名操作
                for path_R_src, path_R_dst in operations.rename:
                    rename_src_dir, rename_src_file = os_path.split(path_R_src)
                    rename_dst_dir, rename_dst_file = os_path.split(path_R_dst)
                    rename_src_path = os_path.join(root_src, path_R_src)
                    rename_dst_path = os_path.join(root_dst, path_R_dst)

                    # 來源不存在則不進行重命名操作
                    if not os_path.exists(rename_src_path):
                        if mirror:
                            self.delete_path.add(rename_dst_path)
                        continue

                    # 若重命名後的目標路徑屬於當前目錄的子/孫樹，則加入保留集
                    if is_parent_dir(rel_src_dir, path_R_dst):
                        filename: str = get_top_dirname(
                            os_path.relpath(path_R_dst, rel_src_dir)
                        )
                        keep_set.add(filename)

                    # 若當前路徑尚未匹配來源路徑的父目錄，則跳過
                    if not fn_filter(
                        [current_dirname], os_path.dirname(rename_src_path)
                    ):
                        continue

                    # 若重命名後的目標路徑在刪除操作中，則將其來源加入刪除集
                    if path_R_dst in operations.delete:
                        names_set: set = set(fn_filter(src_filenames, rename_src_file))
                        delete_set.update(names_set)
                        continue

                    delete_set.add(rename_src_file)
                    keep_set.discard(rename_src_file)
                    self.__set_rename_oper(
                        root_src, root_dst, path_R_src, path_R_dst, operations
                    )

                ignore_set |= delete_set | modify_set
                keep_set |= modify_set | add_set

                inter = keep_set & delete_set
                keep_set -= inter
                delete_set -= inter

            path_dst: str = (
                Pipe(current_dirname)
                .do(os_path.relpath, ..., root_src)
                .do(os_path.join, root_dst, ...)
                .to(os_path.normpath)
                .get()
            )

            # 鏡像模式下清理目標目錄中不在源目錄中的文件
            if mirror and os_path.exists(path_dst):
                self.mirror_oper.append((current_dirname, path_dst, keep_set))

            # logger
            for dele in delete_set:
                logger.trace(f"Ignore src: {os_path.join(current_dirname, dele)}")
            for mod in modify_set:
                logger.trace(f"Skip src: {os_path.join(current_dirname, mod)}")
            for add in add_set:
                logger.trace(f"Keep: {os_path.join(path_dst, add)}")

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
        rename_src_path = os_path.join(root_src, path_R_src)
        rename_dst_path = os_path.join(root_dst, path_R_dst)

        # 若為檔案直接處理即可
        if os_path.isfile(rename_src_path):
            self.rename_oper.append((rename_src_path, rename_dst_path, None))
            return

        # 若為目錄，利用遞迴連帶處理需要被進行操作的子目錄
        oper: Operation = Operation()

        oper.rename = set(
            (rel_src, rel_dst)
            for (x, y) in operations.rename
            if is_parent_dir(path_R_src, x)
            and is_parent_dir(path_R_dst, y)
            and (rel_src := os_path.relpath(x, path_R_src)) != "."
            and (rel_dst := os_path.relpath(y, path_R_dst)) != "."
        )

        oper.modify = set(
            (rel, subdir)
            for (x, subdir) in operations.modify
            if is_parent_dir(path_R_dst, x)
            and (rel := os_path.relpath(x, path_R_dst)) != "."
        )

        oper.delete = set(
            rel
            for x in operations.delete
            if is_parent_dir(path_R_dst, x)
            and (rel := os_path.relpath(x, path_R_dst)) != "."
        )

        oper.apply = set(
            (rel, subdir)
            for (x, subdir) in operations.apply
            if is_parent_dir(path_R_dst, x)
            and (rel := os_path.relpath(x, path_R_dst)) != "."
        )

        oper.build_modify_index()
        oper.build_apply_index()

        self.rename_oper.append((rename_src_path, rename_dst_path, oper))
