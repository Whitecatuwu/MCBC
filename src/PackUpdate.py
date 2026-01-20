from shutil import copytree
from os import path as os_path
from fnmatch import filter as fn_filter
from .file_operation import delete, mirror_cleanup, filtercopy
from .ResPack import ResPack
from .path_utils import is_parent_dir, get_top_dirname
from .Pipe import Pipe
from loguru import logger


class PackUpdate:

    def update(self, pre_ver: ResPack, ver: ResPack, mirror=True) -> None:
        src: str = pre_ver.path
        dst: str = ver.path
        operations: dict[str, list] = ver.get_operations()

        if not os_path.exists(src):
            logger.warning(f'Warning : "{src}" is does not exist.')
            return
        if not os_path.exists(dst):
            logger.warning(f'Warning : "{dst}" is does not exist.')
            return

        self.copydata(
            os_path.join(src, "assets"),
            os_path.join(dst, "assets"),
            operations=operations,
            root_src=src,
            root_dst=dst,
            mirror=mirror,
        )

        if operations is None or operations == {}:
            return
        for MA, sub_dir in operations["M"] | operations["A"]:
            temp = filter(
                lambda x: x != ".",
                [ver.operations_path, sub_dir, os_path.basename(MA)],
            )
            src_update: str = os_path.join(*temp)
            dst_update: str = os_path.join(dst, MA)
            self.copydata(
                src_update,
                dst_update,
                operations=None,
                mirror=mirror,
            )

        for D, _ in operations["D"]:
            if os_path.split(D)[0] == "":
                delete(os_path.join(dst, "**", D))
            else:
                delete(os_path.join(dst, D))

    def copydata(
        self,
        src: str,
        dst: str,
        operations: dict[str, set] = None,
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
                copy_function=filtercopy(ignore_old=ignore_old),
            )
            return
        elif os_path.isfile(src):
            filtercopy(ignore_old=ignore_old)(src, dst)
            return
        else:
            logger.error(
                f'Update failed: {dst} \nBecause: "{src}" is not a directory or a file.\n'
            )

    def __operations(
        self,
        operations: dict[str, set],
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

        operations_is_empty = operations is None or operations == {}

        def __ignore(current_dirname: str, src_filenames: list) -> set:
            # 保留集:避免文件在鏡像模式下被刪除
            keep_set: set[str] = set(src_filenames)
            # 刪除集:移除不需要的文件
            delete_set: set[str] = set()
            # 修改集:需要更新的文件
            modify_set: set[str] = set()
            # 新增集:需要新增的文件
            add_set: set[str] = set()
            # 忽略集:不需要處理的文件，包含修改集和刪除集的文件
            ignore_set: set[str] = set()

            if operations_is_empty:
                pass
            else:
                # 處理刪除集
                for path_D, _ in operations["D"]:
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
                for path_M, _ in operations["M"]:
                    dirname, filename = os_path.split(os_path.join(root_src, path_M))
                    if not fn_filter([current_dirname], dirname):
                        continue
                    names_set: set = set(fn_filter(src_filenames, filename))
                    modify_set.update(names_set)

                # 處理新增集
                for path_A, _ in operations["A"]:
                    path_A = os_path.join(root_src, path_A)
                    if not is_parent_dir(current_dirname, path_A):
                        continue
                    filename = get_top_dirname(os_path.relpath(path_A, current_dirname))
                    if filename not in src_filenames:
                        add_set.add(filename)

                # 處理重命名操作
                for path_R_src, path_R_dst in operations["R"]:
                    rename_src_dir, rename_src_file = os_path.split(path_R_src)
                    rename_dst_dir, rename_dst_file = os_path.split(path_R_dst)
                    rename_src_path = os_path.join(root_src, path_R_src)
                    rename_dst_path = os_path.join(root_dst, path_R_dst)

                    # 若重命名後的目標路徑在當前目錄下，或屬於當前目錄的子目錄，則加入保留集
                    keep_renamed_path: str = os_path.normpath(
                        os_path.join(root_src, rename_dst_dir)
                    )
                    if fn_filter([current_dirname], keep_renamed_path):
                        keep_set.add(rename_dst_file)
                    elif is_parent_dir(current_dirname, keep_renamed_path):
                        filename: str = get_top_dirname(
                            os_path.relpath(keep_renamed_path, current_dirname)
                        )
                        keep_set.add(filename)

                    # 來源不存在則不進行重命名操作
                    if not os_path.exists(rename_src_path):
                        if mirror:
                            delete(rename_dst_path)
                        continue

                    # 若當前路徑不匹配來源路徑的父目錄，則跳過
                    if not fn_filter(
                        [current_dirname], os_path.dirname(rename_src_path)
                    ):
                        continue

                    # 若重命名後的目標路徑在刪除操作中，則將其來源加入刪除集
                    if path_R_dst in (x for x, _ in operations["D"]):
                        names_set: set = set(fn_filter(src_filenames, rename_src_file))
                        delete_set.update(names_set)
                        continue

                    delete_set.add(rename_src_file)
                    keep_set.discard(rename_src_file)

                    # 若為檔案直接處理即可
                    if os_path.isfile(rename_src_path):
                        self.copydata(rename_src_path, rename_dst_path)
                        continue

                    # 若為目錄，利用遞迴連帶處理需要被進行操作的子目錄
                    operations_for_rename: dict[str, set] = {
                        "R": set(),
                        "M": set(),
                        "D": set(),
                        "A": set(),
                    }

                    operations_for_rename["R"] = set(
                        (rel_src, rel_dst)
                        for (x, y) in operations["R"]
                        if is_parent_dir(path_R_src, x)
                        and is_parent_dir(path_R_dst, y)
                        and (rel_src := os_path.relpath(x, path_R_src)) != "."
                        and (rel_dst := os_path.relpath(y, path_R_dst)) != "."
                    )

                    operations_for_rename["M"] = set(
                        (rel, "")
                        for (x, _) in operations["M"]
                        if is_parent_dir(path_R_dst, x)
                        and (rel := os_path.relpath(x, path_R_dst)) != "."
                    )

                    operations_for_rename["D"] = set(
                        (rel, "")
                        for (x, _) in operations["D"]
                        if is_parent_dir(path_R_dst, x)
                        and (rel := os_path.relpath(x, path_R_dst)) != "."
                    )

                    operations_for_rename["A"] = set(
                        (rel, "")
                        for (x, _) in operations["A"]
                        if is_parent_dir(path_R_dst, x)
                        and (rel := os_path.relpath(x, path_R_dst)) != "."
                    )

                    self.copydata(
                        rename_src_path,
                        rename_dst_path,
                        operations=operations_for_rename,
                        mirror=mirror,
                        root_src=rename_src_path,
                        root_dst=rename_dst_path,
                    )
                    logger.trace(f"Rename: {rename_src_path} -> {rename_dst_path}")

                ignore_set = ignore_set | delete_set | modify_set
                keep_set = keep_set | modify_set | add_set
                keep_set.difference_update(delete_set)

            # 鏡像模式下清理目標目錄中不在源目錄中的文件
            if mirror and os_path.exists(
                path_dst := Pipe(current_dirname)
                .do(os_path.relpath, ..., root_src)
                .do(os_path.join, root_dst, ...)
                .to(os_path.normpath)
                .get()
            ):
                mirror_cleanup(current_dirname, path_dst, keep_set)

            for dele in delete_set:
                logger.trace(f"Ignore src: {os_path.join(current_dirname, dele)}")
            for mod in modify_set:
                logger.trace(f"Skip src: {os_path.join(current_dirname, mod)}")
            for add in add_set:
                logger.trace(f"Keep: {os_path.join(path_dst, add)}")

            return ignore_set

        return __ignore
