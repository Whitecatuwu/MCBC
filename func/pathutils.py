import os
import sys
import pathlib
from re import match
from fnmatch import filter as fn_filter


def is_valid_pathname(pathname: str) -> bool:
    ###"""invalid: {\, /, *, ?, :, ", <, >, |}"""
    # assert isinstance(pathname,str)
    pathname = pathname.replace("/", "\\")
    pattern = r'(([a-zA-Z]:\\)|\.{0,2}\\)?([^\\/:*?"<>|]+\\)*([^\\/*?:"<>|]+(\.[^\\/*?:"<>|]+)*)$'
    # pattern = r'(([a-zA-Z]:\\)|\.{0,2}\\)?(\w+\\)*(\w+(\.\w+)*)$'
    return match(pattern, pathname) is not None


def is_parent_dir(path_parent: str, path_child: str) -> bool:
    if len(path_child) < len(path_parent):
        return False

    path_parent = path_parent.replace("/", "\\")
    path_child = path_child.replace("/", "\\")
    spilt_parent = path_parent.split("\\")
    spilt_child = path_child.split("\\")

    for p, c in zip(spilt_parent, spilt_child):
        if not fn_filter([c], p):
            return False
    return True


def get_top_dirname(path: str) -> str:
    assert is_valid_pathname(path)
    path = path.replace("/", "\\").strip("\\")
    return path.split("\\")[0]
