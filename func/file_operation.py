from shutil import copy2, copytree, rmtree
from os import scandir, remove, makedirs, path as os_path
from fnmatch import filter as fn_filter
from .ansi import *
from .path_utils import *
import glob


def mirror_cleanup(
    src_dirname: str, dst_dirname: str, keep_filenames: set = set()
) -> None:
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

        dst_is_older: bool = (not os_path.exists(dst)) or (
            os_path.getmtime(src) > os_path.getmtime(dst)
        )
        if ignore_old and not dst_is_older:
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
    operations_is_empty = operations is None or operations == {}

    def __ignore(current_dirname: str, src_filenames: list) -> set:
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
                    if mirror:
                        delete(rename_dst_path)
                    continue

                if not fn_filter([current_dirname], os_path.dirname(rename_src_path)):
                    continue

                if (path_R_dst,) in operations["D"]:
                    names_set: set = set(fn_filter(src_filenames, rename_src_file))
                    delete_set.update(names_set)
                    continue

                ignore_set.add(rename_src_file)
                keep_set.discard(rename_src_file)

                if os_path.isfile(rename_src_path):
                    copydata(rename_src_path, rename_dst_path)
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

    return __ignore
