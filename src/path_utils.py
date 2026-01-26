from __future__ import annotations
from pathlib import PurePath
from os.path import normpath, join
from os import name as os_name
from fnmatch import filter as fn_filter, fnmatch
from functools import lru_cache


_WINDOWS_DEVICE_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *{f"COM{i}" for i in range(1, 10)},
    *{f"LPT{i}" for i in range(1, 10)},
}

_WINDOWS_INVALID_CHARS = set('<>:"/\\|?*')


def is_valid_pathname(pathname: str) -> bool:
    """
    驗證路徑是否有非法字元。
    注意：不代表路徑存在；僅代表字串在當前 OS 的一般規則下可用。
    """
    if not isinstance(pathname, str):
        return False

    if pathname == "":
        return False

    # Null byte
    if "\0" in pathname:
        return False

    # 控制字元（0-31）
    if any(ord(ch) < 32 for ch in pathname):
        return False

    # 以當前 OS 規則檢查
    if os_name == "nt":
        # 分隔符統一（方便逐段檢查）
        p = pathname.replace("/", "\\")
        # 不允許 UNC/長路徑前綴等（視需求，可放寬）
        # if p.startswith("\\\\") or p.startswith("\\\\?\\"):
        #     return False

        # 逐段檢查（允許分隔符，但片段內不能有非法字元）
        parts = [seg for seg in p.split("\\") if seg != ""]
        for seg in parts:
            # 片段不能包含 Windows 非法字元
            if any(ch in _WINDOWS_INVALID_CHARS for ch in seg):
                return False

            # 片段不能以空白或句點結尾
            if seg.endswith(" ") or seg.endswith("."):
                return False

            # 裝置保留名（去掉副檔名後比較）
            stem = seg.split(".", 1)[0].upper()
            if stem in _WINDOWS_DEVICE_NAMES:
                return False

        return True

    else:
        # POSIX：唯一必殺通常是 NUL（已檢查）
        # 你也可以視需求禁止 "/" 出現在片段內（但 POSIX "/" 本來就是分隔符）
        return True


def is_parent_dir(parent: str, child_pattern: str) -> bool:
    parent_parts: tuple = path_split(parent)
    child_parts: tuple = path_split(child_pattern)

    # 逐節點比對：萬用字元只作用在「單一節點」
    for p, c in zip(parent_parts, child_parts):
        if c == "**":
            return True
        if not fnmatch(p, c):
            return False

    return len(child_parts) >= len(parent_parts)


def get_top_dirname(path: str) -> str:
    p = PurePath(normpath(path))
    if str(p) in ("", "."):
        return ""
    parts = p.parts
    return "" if not parts or parts[0] == "." else parts[0]


def path_split(path: str) -> tuple:
    p = PurePath(normpath(path))
    return p.parts


def has_matching_part(path: str, part: str) -> bool:
    parts: list = path_split(path)
    return any(fn_filter(parts, part))


def is_path_match(parent_path: str, child_pattern: str) -> bool:
    parent: tuple = path_split(parent_path)
    raw_pat: tuple = path_split(child_pattern)

    # Collapse consecutive '**' to a single one
    pat = []
    for seg in raw_pat:
        if seg == "**" and pat and pat[-1] == "**":
            continue
        pat.append(seg)
    pat = tuple(pat)  # make hashable for caching

    @lru_cache(maxsize=None)
    def match(i: int, j: int) -> bool:
        if i == len(pat):
            return j == len(parent)
        if j == len(parent):
            return all(seg == "**" for seg in pat[i:])

        token = pat[i]

        if token == "**":
            # Match zero segments (advance pattern) OR consume one parent segment
            return match(i + 1, j) or match(i, j + 1)

        # Normal segment must match the current parent segment
        if fnmatch(parent[j], token):
            return match(i + 1, j + 1)

        return False

    return match(0, 0)


def path_merge(head: str, *tails: str) -> str:
    return normpath(join(head, *tails))


"""def is_same_path(path1, path2):
    return Path(path1).resolve(strict=False) == Path(path2).resolve(strict=False)"""

if __name__ == "__main__":
    # Simple testss

    assert is_path_match("a/b/c", "b/c") is False
    assert is_path_match("a/b/c", "**/c") is True
    assert is_path_match("a/b", "a/b/**") is True
    assert is_path_match("a/b/c", "a/**/c") is True
    assert is_path_match("a/b/c", "a/**") is True
    assert is_path_match("a/b/c", "a/**/d") is False
