from shutil import copy2, copytree, rmtree
from os import scandir, remove, makedirs, path as os_path
from fnmatch import filter as fn_filter
from .ansi import *
from .pathutils import *
from .ResPack import ResPack


def mirror_cleanup(
    src_dirname: str, dst_dirname: str, keep_filenames: set = set()
) -> None:
    if not os_path.isdir(src_dirname):
        raise ValueError(f"{src_dirname} must be a directory.")
    if not os_path.isdir(dst_dirname):
        raise ValueError(f"{dst_dirname} must be a directory.")
    if os_path.samefile(src_dirname, dst_dirname):
        raise ValueError("Source and destination directories must be different.")

    src_filenames = set(map(lambda x: x.name, scandir(src_dirname)))
    for d in scandir(dst_dirname):
        if d.name in src_filenames or d.name in keep_filenames:
            continue
        delete(d.path)


def filtercopy(ignore_old=True) -> callable:
    def _filter(src, dst) -> None:
        dst_is_older: bool = (not os_path.exists(dst)) or (
            os_path.getmtime(src) > os_path.getmtime(dst)
        )
        if ignore_old and (not dst_is_older):
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
    if not os_path.exists(pathname):
        return
    try:
        rmtree(pathname) if os_path.isdir(pathname) else remove(pathname)
    except Exception as e:
        print(Red(f"Delete failed: {pathname} \nBecause: {e}\n"))
    else:
        print(Purple(f"Delete: {pathname}"))


def copydata(
    src: str,
    dst: str,
    operations: dict[str, set] = None,
    root_src: str = None,
    root_dst: str = None,
    mirror: bool = False,
    ignore_old: bool = True,
) -> bool:
    if not os_path.exists(src):
        print(Red(f'Update failed: {dst} \nBecause: "{src}" does not exist.\n'))
        return False
    if os_path.isdir(src):
        root_src = src if root_src == None else root_src
        root_dst = dst if root_dst == None else root_dst
        copytree(
            src,
            dst,
            dirs_exist_ok=True,
            ignore=_operations(operations, root_src, root_dst, mirror=mirror),
            copy_function=filtercopy(ignore_old=ignore_old),
        )
        return True
    elif os_path.isfile(src):
        filtercopy(ignore_old=ignore_old)(src, dst)
        return True
    else:
        print(
            Red(
                f'Update failed: {dst} \nBecause: "{src}" is not a directory or a file.\n'
            )
        )
        return False


def _operations(
    operations: dict[str, set],
    root_src: str,
    root_dst: str,
    mirror: bool = False,
) -> callable:
    operations_is_empty = operations is None or operations == {}

    def _ignore(current_dirname: str, src_filenames: list) -> set:
        keep_set: set[str] = set(src_filenames)
        delete_set: set[str] = set()
        modify_set: set[str] = set()
        add_set: set[str] = set()
        ignore_set: set[str] = set()

        if operations_is_empty:
            pass
        else:
            for (path_D,) in operations["D"]:
                dirname, filename = os_path.split(os_path.join(root_src, path_D))
                is_global_ignore: bool = os_path.normpath(dirname) == os_path.normpath(
                    root_src
                )
                if not fn_filter([current_dirname], dirname) and not is_global_ignore:
                    continue
                names_set: set = set(fn_filter(src_filenames, filename))
                delete_set.update(names_set)
                """if not names_set and not is_global_ignore:
                    print(
                        Yellow(
                            f'Warning : There were no results found for {filename} in "{dirname}".'
                        )
                    )"""

            for (path_M,) in operations["M"]:
                dirname, filename = os_path.split(os_path.join(root_src, path_M))
                if not fn_filter([current_dirname], dirname):
                    continue
                names_set: set = set(fn_filter(src_filenames, filename))
                modify_set.update(names_set)
                """if not names_set:
                    print(
                        Yellow(
                            f'Warning : There were no results found for {filename} in "{dirname}".'
                        )
                    )"""

            for (path_A,) in operations["A"]:
                path_A = os_path.join(root_src, path_A)
                if not is_parent_dir(current_dirname, path_A):
                    continue
                filename = get_top_dirname(os_path.relpath(path_A, current_dirname))
                if filename not in src_filenames:
                    add_set.add(filename)

            for path_R_src, path_R_dst in operations["R"]:
                rename_src_dir, rename_src_file = os_path.split(path_R_src)
                rename_dst_dir, rename_dst_file = os_path.split(path_R_dst)
                rename_src_path = os_path.join(root_src, path_R_src)
                rename_dst_path = os_path.join(root_dst, path_R_dst)

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

                if not os_path.exists(rename_src_path):
                    continue

                if not fn_filter([current_dirname], os_path.dirname(rename_src_path)):
                    continue

                if (path_R_dst,) in operations["D"]:
                    names_set: set = set(fn_filter(src_filenames, rename_src_file))
                    delete_set.update(names_set)
                    continue

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
                    (rel,)
                    for (x,) in operations["M"]
                    if is_parent_dir(path_R_dst, x)
                    and (rel := os_path.relpath(x, path_R_dst)) != "."
                )

                operations_for_rename["D"] = set(
                    (rel,)
                    for (x,) in operations["D"]
                    if is_parent_dir(path_R_dst, x)
                    and (rel := os_path.relpath(x, path_R_dst)) != "."
                )

                operations_for_rename["A"] = set(
                    (rel,)
                    for (x,) in operations["A"]
                    if is_parent_dir(path_R_dst, x)
                    and (rel := os_path.relpath(x, path_R_dst)) != "."
                )

                ignore_set.add(rename_src_file)
                keep_set.discard(rename_src_file)
                copydata(
                    rename_src_path,
                    rename_dst_path,
                    operations=operations_for_rename,
                    mirror=True,
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

        if mirror and os_path.exists(
            path_dst := os_path.normpath(
                os_path.join(root_dst, os_path.relpath(current_dirname, root_src))
            )
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

    return _ignore


def update(pre_ver: ResPack, ver: ResPack, mirror=True) -> None:
    src: str = pre_ver.path
    dst: str = ver.path
    operations: dict[str, list] = ver.get_operations()

    if not os_path.exists(src):
        print(Yellow(f'Warning : "{src}" is does not exist.'))
        return
    if not os_path.exists(dst):
        print(Yellow(f'Warning : "{dst}" is does not exist.'))
        return

    copydata(
        os_path.join(src, "assets"),
        os_path.join(dst, "assets"),
        operations=operations,
        root_src=src,
        root_dst=dst,
        mirror=mirror,
    )

    if operations is None or operations == {}:
        return
    for (M,) in operations["M"]:
        src_update: str = os_path.join(ver.operations_path, os_path.basename(M))
        dst_update: str = os_path.join(dst, M)
        if not os_path.exists(src_update):
            # print(Yellow(f"Can't find {src_update}"))
            src_update = os_path.join(src, M)
        if not os_path.exists(src_update):
            if mirror:
                delete(dst_update)
            continue
        copydata(
            src_update,
            dst_update,
            operations=None,
            mirror=mirror,
        )

    for (A,) in operations["A"]:
        src_update: str = os_path.join(ver.operations_path, os_path.basename(A))
        dst_update: str = os_path.join(dst, A)
        if not os_path.exists(src_update):
            if mirror:
                delete(dst_update)
            continue
        copydata(
            src_update,
            dst_update,
            operations=None,
            mirror=mirror,
        )
    for (D,) in operations["D"]:
        delete(os_path.join(dst, D))
