from __future__ import annotations
from pathlib import Path
from os.path import normpath, commonpath
from os import name as os_name


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


def is_parent_dir(path_parent: str, path_child: str) -> bool:
    path_parent = normpath(path_parent)
    path_child = normpath(path_child)
    try:
        return commonpath([path_parent, path_child]) == path_parent
    except ValueError:
        return False


def get_top_dirname(path: str) -> str:
    p = Path(normpath(path))
    if str(p) in ("", "."):
        return ""
    parts = p.parts
    return "" if not parts or parts[0] == "." else parts[0]


def path_split(path: str) -> list:
    p = Path(normpath(path))
    return list(p.parts)


"""def is_same_path(path1, path2):
    return Path(path1).resolve(strict=False) == Path(path2).resolve(strict=False)"""

if __name__ == "__main__":
    print(is_parent_dir(r"assets/item", r"assets/item"))
