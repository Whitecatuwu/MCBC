from shutil import copy2, copytree, rmtree
from os import chdir, scandir, remove, path as os_path, makedirs
from time import time as current_time
from fnmatch import filter as fn_filter
from func.ansi import *
from func.pathutils import *
from func.ResPack import ResPack

# import threading

CURRENT_DIR = os_path.dirname(os_path.abspath(__file__))


def filtercopy(ignore_old=True) -> callable:
    ##Ignore older files when ignore_old is True.
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
    operations: dict[str, list] = None,
    root_src: str = None,
    root_dst: str = None,
    purge: bool = False,
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
            ignore=_operations(operations, root_src, root_dst, purge=purge),
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
    operations: dict[str, list],
    root_src: str,
    root_dst: str,
    purge: bool = False,
) -> callable:
    def _ignore(current_dirname: str, src_filenames: list) -> set:
        keep_set: set[str] = set(src_filenames)
        delete_set: set[str] = set()
        modify_set: set[str] = set()
        add_set: set[str] = set()
        ignore_set: set[str] = set()

        if operations is None or operations == {}:
            pass
        else:
            # fn_filter(names, pattern)
            dirname: str
            filename: str

            for path_D in operations["D"]:
                path_D: str = path_D[0]
                path_D = os_path.join(root_src, path_D)
                dirname, filename = os_path.split(path_D)
                if not fn_filter([current_dirname], dirname) and dirname != root_src:
                    continue
                names_set: set = set(fn_filter(src_filenames, filename))
                delete_set.update(names_set)
                if not names_set and dirname != root_src:
                    print(
                        Yellow(
                            f'Warning : There were no results found for {filename} in "{dirname}".'
                        )
                    )

            for path_M in operations["M"]:
                path_M: str = path_M[0]
                path_M = os_path.join(root_src, path_M)
                dirname, filename = os_path.split(path_M)
                if not fn_filter([current_dirname], dirname) and dirname != root_src:
                    continue
                names_set: set = set(fn_filter(src_filenames, filename))
                modify_set.update(names_set)
                if not names_set and (not dirname == root_src):
                    print(
                        Yellow(
                            f'Warning : There were no results found for {filename} in "{dirname}".'
                        )
                    )

            for path_A in operations["A"]:
                path_A: str = path_A[0]
                path_A = os_path.join(root_src, path_A)
                if not is_parent_dir(current_dirname, path_A):
                    continue
                filename = get_top_dirname(os_path.relpath(path_A, current_dirname))
                if filename not in src_filenames:
                    add_set.add(filename)

            for path_R in operations["R"]:
                path_R_src: str = path_R[0]
                path_R_dst: str = path_R[1]
                rename_src_dir, rename_src_file = os_path.split(path_R_src)
                rename_dst_dir, rename_dst_file = os_path.split(path_R_dst)
                rename_src_path = os_path.join(root_src, path_R_src)
                rename_dst_path = os_path.join(root_dst, path_R_dst)
                # assert is_valid_pathname(rename_src_path) and is_valid_pathname(rename_dst_path)

                if fn_filter([current_dirname], os_path.dirname(rename_src_path)):
                    operations_for_rename: dict[str, list] = {
                        "R": [],
                        "M": [],
                        "D": [],
                        "A": [],
                    }
                    operations_for_rename["R"] = [
                        (
                            (
                                os_path.relpath(x, path_R[0])
                                if is_parent_dir(path_R[0], x)
                                else "."
                            ),
                            (
                                os_path.relpath(y, path_R[1])
                                if is_parent_dir(path_R[1], y)
                                else "."
                            ),
                        )
                        for (x, y) in operations["R"]
                    ]
                    operations_for_rename["R"] = [
                        (x, y)
                        for (x, y) in operations_for_rename["R"]
                        if x != "." and y != "."
                    ]

                    operations_for_rename["M"] = [
                        (
                            tuple([os_path.relpath(x[0], path_R[1])])
                            if is_parent_dir(path_R[1], x[0])
                            else "."
                        )
                        for x in operations["M"]
                    ]
                    operations_for_rename["M"] = [
                        x for x in operations_for_rename["M"] if x != (".")
                    ]

                    operations_for_rename["D"] = [
                        (
                            tuple([os_path.relpath(x[0], path_R[1])])
                            if is_parent_dir(path_R[1], x[0])
                            else "."
                        )
                        for x in operations["D"]
                    ]
                    operations_for_rename["D"] = [
                        x for x in operations_for_rename["D"] if x != (".")
                    ]

                    operations_for_rename["A"] = [
                        (
                            tuple([os_path.relpath(x[0], path_R[1])])
                            if is_parent_dir(path_R[1], x[0])
                            else "."
                        )
                        for x in operations["A"]
                    ]
                    operations_for_rename["A"] = [
                        x for x in operations_for_rename["A"] if x != (".")
                    ]

                    ignore_set.add(rename_src_file)
                    keep_set.discard(rename_src_file)
                    copydata(
                        rename_src_path,
                        rename_dst_path,
                        operations=operations_for_rename,
                        purge=True,
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

                keep_renamed_path: str = os_path.join(root_src, rename_dst_dir)
                keep_renamed_path = os_path.normpath(keep_renamed_path)
                if fn_filter([current_dirname], keep_renamed_path):
                    keep_set.add(rename_dst_file)
                elif is_parent_dir(current_dirname, keep_renamed_path):
                    filename = get_top_dirname(
                        os_path.relpath(keep_renamed_path, current_dirname)
                    )
                    keep_set.add(filename)

            ignore_set = ignore_set | delete_set | modify_set
            keep_set = keep_set | modify_set | add_set
            keep_set.difference_update(delete_set)

        if purge and os_path.exists(
            path_dst := os_path.normpath(
                os_path.join(root_dst, os_path.relpath(current_dirname, root_src))
            )
        ):
            for d in scandir(path_dst):
                if d.name not in keep_set:
                    delete(d.path)

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


def update(pre_ver: ResPack, ver: ResPack) -> None:
    src: str = pre_ver.path
    dst: str = ver.path
    operations: dict[str, list] = ver.get_operations()

    if not os_path.exists(src):
        print(Yellow(f'Warning : "{src}" is does not exist.'))
        return
    if not os_path.exists(dst):
        print(Yellow(f'Warning : "{dst}" is does not exist.'))
        return

    # Copy files that not in ignore list and not in operations.
    copydata(
        os_path.join(src, "assets"),
        os_path.join(dst, "assets"),
        operations=operations,
        root_src=src,
        root_dst=dst,
        purge=True,
    )

    if operations is None or operations == {}:
        return
    for MA in operations["M"] + operations["A"]:
        s: str = os_path.join(ver.operations_path, os_path.basename(MA[0]))
        d: str = os_path.join(dst, MA[0])
        copydata(
            s,
            d,
            operations=None,
            purge=True,
            root_src=s,
            root_dst=d,
        )
    for D in operations["D"]:
        delete(os_path.join(dst, D[0]))


def main():
    older_vers = ["", "1.16.5", "1.16.1", "1.14.4", "1.12.2", "1.10.2", "1.8.9"]
    vers = [
        "",
        "1.17.1",
        "1.18.2",
        "1.19.2",
        "1.19.3",
        "1.19.4",
        "1.20.1",
        "1.20.2",
        "1.20.4",
        "1.20.6",
        "1.21.1",
        "1.21.3",
        "1.21.4",
        "1.21.5",
    ]

    ver_res_packs = []
    for ver in vers:
        if ver == "":
            pack = ResPack(os_path.join(CURRENT_DIR, "battlecats"), ver)
        else:
            pack = ResPack(
                os_path.join(CURRENT_DIR, "battlecats_" + ver),
                ver,
                os_path.join(CURRENT_DIR, "battlecats", "vers", ver),
            )
        ver_res_packs.append(pack)

    older_ver_res_packs = []
    for old in older_vers:
        if old == "":
            pack = ResPack(os_path.join(CURRENT_DIR, "battlecats"), old)
        else:
            pack = ResPack(
                os_path.join(CURRENT_DIR, "battlecats_" + old),
                old,
                os_path.join(CURRENT_DIR, "battlecats", "vers", old),
            )
        older_ver_res_packs.append(pack)

    # locks = threading.Lock()

    def update_older() -> None:
        for i in range(1, len(older_ver_res_packs), 1):
            print(Strong(f"{older_ver_res_packs[i].version():-^50}"))
            update(older_ver_res_packs[i - 1], older_ver_res_packs[i])

    def update_newer() -> None:
        for i in range(1, len(ver_res_packs), 1):
            print(Strong(f"{ver_res_packs[i].version():-^50}"))
            update(ver_res_packs[i - 1], ver_res_packs[i])

    # older = threading.Thread(target=update_older)
    # older.start()

    update_older()
    update_newer()


if __name__ == "__main__":
    chdir(CURRENT_DIR)
    while True:
        try:
            start_time = current_time()
            main()
            print("\nFinish.")
            print("runtime: %s seconds" % (current_time() - start_time))
            c = input("Press Enter to continue or -1 to exit...\n")
            if c == "-1":
                break
        except Exception as e:
            # print(Red(f"Error: {e}"))
            raise e
            break
