from shutil import copy2, copytree, rmtree
from os import chdir, scandir, remove, path, makedirs
from time import time as current_time
from fnmatch import filter as fn_filter
from func.ansi import *
from func.pathutils import *
from func.ResPack import ResPack

# import threading

current = path.dirname(path.abspath(__file__))
chdir(current)


def filtercopy(ignore_old=True, _: list = [False]) -> callable:
    ##Ignore older files when ignore_old is True.
    def _filter(src, dst) -> None:
        dst_is_older: bool = (not path.exists(dst)) or (
            path.getmtime(src) > path.getmtime(dst)
        )
        if ignore_old and (not dst_is_older):
            return

        dst_dir = path.dirname(dst)
        if not path.exists(dst_dir):
            makedirs(dst_dir)
        try:
            copy2(src, dst)
        except Exception as e:
            print(Red(f"Update failed: {dst} \nBecause: {e}\n"))
        else:
            print(Green(f"Update: {dst}"))
            _[0] = True

    return _filter


def delete(pathname: str) -> None:
    if not path.exists(pathname):
        return
    try:
        rmtree(pathname) if path.isdir(pathname) else remove(pathname)
    except Exception as e:
        print(Red(f"Delete failed: {pathname} \nBecause: {e}\n"))
    else:
        print(Purple(f"Delete: {pathname}"))


def copydata(
    src: str,
    dst: str,
    ignorelists: dict[str, list] = None,
    namespace_src: str = None,
    namespace_dst: str = None,
    purge: bool = False,
    ignore_old: bool = True,
    _: list = [False],
) -> bool:
    if not path.exists(src):
        print(Red(f'Update failed: {dst} \nBecause: "{src}" does not exist.\n'))
        return False
    if path.isdir(src):
        namespace_src = src if namespace_src == None else namespace_src
        namespace_dst = dst if namespace_dst == None else namespace_dst
        copytree(
            src,
            dst,
            dirs_exist_ok=True,
            ignore=_ignorepath(ignorelists, namespace_src, namespace_dst, purge=purge),
            copy_function=filtercopy(ignore_old=ignore_old, _=_),
        )
        return _[0]
    elif path.isfile(src):
        filtercopy(ignore_old=ignore_old, _=_)(src, dst)
        return _[0]
    else:
        print(
            Red(
                f'Update failed: {dst} \nBecause: "{src}" is not a directory or a file.\n'
            )
        )
        return False


def _ignorepath(
    pathlists: dict[str, list],
    namespace_src: str,
    namespace_dst: str,
    purge: bool = False,
) -> callable:
    def _ignore(current_dirname: str, src_filenames: list) -> set:
        keep_set: set[str] = set(src_filenames)
        delete_set: set[str] = set()
        modify_set: set[str] = set()
        add_set: set[str] = set()
        ignore_set: set[str] = set()

        if pathlists == {} or pathlists is None:
            pass
        else:
            # fn_filter(names, pattern)
            dirname: str
            filename: str

            for path_D in pathlists["D"]:
                path_D: str = path_D[0]
                path_D = path.join(namespace_src, path_D)
                dirname, filename = path.split(path_D)
                if fn_filter([current_dirname], dirname) or dirname == namespace_src:
                    names_set: set = set(fn_filter(src_filenames, filename))
                    delete_set.update(names_set)
                    if not names_set and (not dirname == namespace_src):
                        print(
                            Yellow(
                                f'Warning : There were no results found for {filename} in "{dirname}".'
                            )
                        )

            for path_M in pathlists["M"]:
                path_M: str = path_M[0]
                path_M = path.join(namespace_src, path_M)
                # assert is_valid_pathname(path_M)
                dirname, filename = path.split(path_M)
                if fn_filter([current_dirname], dirname) or dirname == namespace_src:
                    names_set: set = set(fn_filter(src_filenames, filename))
                    modify_set.update(names_set)
                    if not names_set and (not dirname == namespace_src):
                        print(
                            Yellow(
                                f'Warning : There were no results found for {filename} in "{dirname}".'
                            )
                        )

            for path_A in pathlists["A"]:
                path_A: str = path_A[0].strip("\\")
                add_path: str = path.join(namespace_src, path_A)
                # assert is_valid_pathname(add_path)
                if is_parent_dir(current_dirname, add_path):
                    filename = get_top_dirname(add_path.replace(current_dirname, ""))
                    if filename not in src_filenames:
                        add_set.add(filename)

            for path_R in pathlists["R"]:
                rename_src_dir, rename_src_file = path.split(path_R[0].strip("\\"))
                rename_dst_dir, rename_dst_file = path.split(path_R[1].strip("\\"))
                rename_src_path = path.join(namespace_src, path_R[0].strip("\\"))
                rename_dst_path = path.join(namespace_dst, path_R[1].strip("\\"))
                # assert is_valid_pathname(rename_src_path) and is_valid_pathname(rename_dst_path)

                if fn_filter([current_dirname], path.dirname(rename_src_path)):
                    pathlists_for_rename: dict[str, list] = {
                        "R": [],
                        "M": [],
                        "D": [],
                        "A": [],
                    }
                    pathlists_for_rename["R"] = [
                        (
                            (
                                x.replace(path_R[0], "").strip("\\")
                                if is_parent_dir(path_R[0], x)
                                else ""
                            ),
                            (
                                y.replace(path_R[1], "").strip("\\")
                                if is_parent_dir(path_R[1], y)
                                else ""
                            ),
                        )
                        for (x, y) in pathlists["R"]
                    ]
                    pathlists_for_rename["R"] = [
                        (x, y)
                        for (x, y) in pathlists_for_rename["R"]
                        if x != "" and y != ""
                    ]

                    pathlists_for_rename["M"] = [
                        (
                            tuple([x[0].replace(path_R[1], "").strip("\\")])
                            if is_parent_dir(path_R[1], x[0])
                            else ""
                        )
                        for x in pathlists["M"]
                    ]
                    pathlists_for_rename["M"] = [
                        x for x in pathlists_for_rename["M"] if x != ("")
                    ]

                    pathlists_for_rename["D"] = [
                        (
                            tuple([x[0].replace(path_R[1], "").strip("\\")])
                            if is_parent_dir(path_R[1], x[0])
                            else ""
                        )
                        for x in pathlists["D"]
                    ]
                    pathlists_for_rename["D"] = [
                        x for x in pathlists_for_rename["D"] if x != ("")
                    ]

                    pathlists_for_rename["A"] = [
                        (
                            tuple([x[0].replace(path_R[1], "").strip("\\")])
                            if is_parent_dir(path_R[1], x[0])
                            else ""
                        )
                        for x in pathlists["A"]
                    ]
                    pathlists_for_rename["A"] = [
                        x for x in pathlists_for_rename["A"] if x != ("")
                    ]

                    ignore_set.add(rename_src_file)
                    keep_set.discard(rename_src_file)
                    copydata(
                        rename_src_path,
                        rename_dst_path,
                        ignorelists=pathlists_for_rename,
                        purge=True,
                        namespace_src=rename_src_path,
                        namespace_dst=rename_dst_path,
                    )
                    """print(
                        Orange(
                            'Rename: "{}" \n -> "{}"\n'.format(
                                path.relpath(rename_src_path, current),
                                path.relpath(rename_dst_path, current),
                            )
                        )
                    )"""

                keep_renamed_path: str = path.join(namespace_src, rename_dst_dir).strip(
                    "\\"
                )
                if fn_filter([current_dirname], keep_renamed_path):
                    keep_set.add(rename_dst_file)
                elif is_parent_dir(current_dirname, keep_renamed_path):
                    filename = get_top_dirname(
                        keep_renamed_path.replace(current_dirname, "")
                    )
                    keep_set.add(filename)

            ignore_set = ignore_set | delete_set | modify_set
            keep_set = keep_set | modify_set | add_set
            keep_set.difference_update(delete_set)

        if (purge == True) and path.exists(
            path_dst := current_dirname.replace(namespace_src, namespace_dst)
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

    if not path.exists(src):
        print(Yellow(f'Warning : "{src}" is does not exist.'))
        return
    if not path.exists(dst):
        print(Yellow(f'Warning : "{dst}" is does not exist.'))
        return

    # Copy files that not in ignore list and not in operations.
    copydata(
        path.join(src, "assets"),
        path.join(dst, "assets"),
        ignorelists=operations,
        namespace_src=src,
        namespace_dst=dst,
        purge=True,
    )

    if operations is None or operations == {}:
        return
    for MA in operations["M"] + operations["A"]:
        s: str = path.join(ver.operations_path, path.basename(MA[0]))
        d: str = path.join(dst, MA[0])
        copydata(
            s,
            d,
            ignorelists={},
            purge=True,
            namespace_src=s,
            namespace_dst=d,
        )
    for D in operations["D"]:
        delete(path.join(dst, D[0]))


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
            pack = ResPack(path.join(current, "battlecats"), ver)
        else:
            pack = ResPack(
                path.join(current, "battlecats_" + ver),
                ver,
                path.join(current, "battlecats", "vers", ver),
            )
        ver_res_packs.append(pack)

    older_ver_res_packs = []
    for old in older_vers:
        if old == "":
            pack = ResPack(path.join(current, "battlecats"), old)
        else:
            pack = ResPack(
                path.join(current, "battlecats_" + old),
                old,
                path.join(current, "battlecats", "vers", old),
            )
        older_ver_res_packs.append(pack)

    # locks = threading.Lock()

    def update_older() -> None:
        # for i in range(1,2,1):
        for i in range(1, len(older_ver_res_packs), 1):
            print(Strong("-" * 25 + older_ver_res_packs[i].version() + "-" * 25))
            update(older_ver_res_packs[i - 1], older_ver_res_packs[i])

    def update_newer() -> None:
        # for i in range(1,2,1):
        for i in range(1, len(ver_res_packs), 1):
            print(Strong("-" * 25 + ver_res_packs[i].version() + "-" * 25))
            update(ver_res_packs[i - 1], ver_res_packs[i])

    # older = threading.Thread(target=update_older)
    # older.start()

    update_older()
    update_newer()


if __name__ == "__main__":
    start_time = current_time()
    main()
    print("\nFinish.")
    print("runtime: %s seconds" % (current_time() - start_time))
    # input("Press Enter to continue...")
