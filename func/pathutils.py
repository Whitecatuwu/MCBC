from pathlib import Path
from re import match
from os.path import normpath, commonpath


def is_valid_pathname(pathname: str) -> bool:
    ###"""invalid: {\, /, *, ?, :, ", <, >, |}"""
    # assert isinstance(pathname,str)
    pathname = pathname.replace("/", "\\")
    pattern = r'(([a-zA-Z]:\\)|\.{0,2}\\)?([^\\/:*?"<>|]+\\)*([^\\/*?:"<>|]+(\.[^\\/*?:"<>|]+)*)$'
    # pattern = r'(([a-zA-Z]:\\)|\.{0,2}\\)?(\w+\\)*(\w+(\.\w+)*)$'
    return match(pattern, pathname) is not None


def is_parent_dir(path_parent: str, path_child: str) -> bool:
    path_parent = normpath(path_parent)
    path_child = normpath(path_child)

    return commonpath([path_parent, path_child]) == path_parent


def get_top_dirname(path: str) -> str:
    assert is_valid_pathname(path)
    return Path(normpath(path)).parts[0]
    # path = path.replace("/", "\\").strip("\\")
    # return path.split("\\")[0]


"""def is_same_path(path1, path2):
    return Path(path1).resolve(strict=False) == Path(path2).resolve(strict=False)"""

if __name__ == "__main__":
    print(is_parent_dir(r"assets/item", r"assets/item"))
