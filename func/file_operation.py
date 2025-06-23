from shutil import copy2, copytree, rmtree
from os import scandir, remove, makedirs, path as os_path
from fnmatch import filter as fn_filter
from .gui.ansi import *
from .path_utils import *
from .Pipe import Pipe
import glob


def mirror_cleanup(
    src_dirname: str, dst_dirname: str, keep_filenames: set = set()
) -> None:
    """
    清理目標目錄中不在源目錄中的文件。
    src_dirname: 源目錄路徑，必須存在且為目錄。
    dst_dirname: 目標目錄路徑，必須存在且為目錄。
    keep_filenames: 保留的文件名集合，這些文件不會被刪除。
    """
    if not os_path.isdir(src_dirname):
        raise TypeError(f"{src_dirname} must be a directory.")
    if not os_path.isdir(dst_dirname):
        raise TypeError(f"{dst_dirname} must be a directory.")
    if os_path.samefile(src_dirname, dst_dirname):
        raise ValueError("Source and destination directories must be different.")

    src_filenames = set(map(lambda x: x.name, scandir(src_dirname)))
    for d in scandir(dst_dirname):
        if d.name in src_filenames or d.name in keep_filenames:
            continue
        delete(d.path)


def filtercopy(ignore_old: bool = True) -> callable:
    def _filter(src: str, dst: str) -> None:
        if not os_path.isfile(src):
            raise TypeError(f"{src} must be a file.")
        if os_path.isdir(dst):
            raise TypeError(f"{dst} must be a file.")

        dst_is_newer: bool = (os_path.exists(dst)) and (
            os_path.getmtime(src) <= os_path.getmtime(dst)
        )
        if ignore_old and dst_is_newer:
            return

        dst_dir = os_path.dirname(dst)
        if not os_path.exists(dst_dir):
            makedirs(dst_dir)
        try:
            copy2(src, dst)
        except Exception as e:
            print(Red(f"Update failed: {dst} \nBecause: {e}\n"))
        else:
            print(Green(f"Update: {dst}"))

    return _filter


def delete(pathname: str) -> None:
    matched_paths = glob.glob(pathname, recursive=True)
    if not matched_paths:
        return
    for matched in matched_paths:
        try:
            if os_path.isdir(matched):
                rmtree(matched)
            else:
                remove(matched)
        except Exception as e:
            print(Red(f"Delete failed: {matched}\nReason: {e}\n"))
        else:
            print(Purple(f"Delete: {matched}"))


def copydata(
    src: str,
    dst: str,
    operations: dict[str, set] = None,
    root_src: str = None,
    root_dst: str = None,
    mirror: bool = False,
    ignore_old: bool = True,
) -> None:
    if not os_path.exists(src):
        print(Red(f'Update failed: {dst} \nBecause: "{src}" does not exist.\n'))
        return
    if os_path.isdir(src):
        root_src = src if root_src == None else root_src
        root_dst = dst if root_dst == None else root_dst
        copytree(
            src,
            dst,
            dirs_exist_ok=True,
            ignore=__operations(operations, root_src, root_dst, mirror=mirror),
            copy_function=filtercopy(ignore_old=ignore_old),
        )
        return
    elif os_path.isfile(src):
        filtercopy(ignore_old=ignore_old)(src, dst)
        return
    else:
        print(
            Red(
                f'Update failed: {dst} \nBecause: "{src}" is not a directory or a file.\n'
            )
        )


def __operations(
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
                is_global_ignore: bool = os_path.normpath(dirname) == os_path.normpath(
                    root_src
                )
                if not fn_filter([current_dirname], dirname) and not is_global_ignore:
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
                if not fn_filter([current_dirname], os_path.dirname(rename_src_path)):
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
                    copydata(rename_src_path, rename_dst_path)
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

                copydata(
                    rename_src_path,
                    rename_dst_path,
                    operations=operations_for_rename,
                    mirror=mirror,
                    root_src=rename_src_path,
                    root_dst=rename_dst_path,
                )
                """print(
                    Orange(
                        'Rename: "{}" \n -> "{}"\n'.format(
                            path.relpath(rename_src_path, current),
                            path.relpath(rename_dst_path, current),
                        )
                    )
                )"""

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

        """for dele in delete_set:
            print(
                Grey(
                    f"Ignore src: {path.relpath(path.join(current_dirname,dele),current)}"
                )
            )
        for mod in modify_set:
            print(
                Cyan(
                    f"Skip src: {path.relpath(path.join(current_dirname,mod),current)}"
                )
            )
        for add in add_set:
            print(Blue(f"Keep: {path.relpath(path.join(path_dst,add),current)}"))"""

        return ignore_set

    return __ignore
