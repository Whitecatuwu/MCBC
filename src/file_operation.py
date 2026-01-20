from shutil import copy2, rmtree
from os import scandir, remove, makedirs, path as os_path
from .gui.ansi import Green, Purple
from loguru import logger
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
            logger.error(f"Copy failed: {src} to {dst} \nBecause: {e}\n")
        else:
            logger.info(Green(f"Update: {dst}"))
            # print(Green(f"Update: {dst}"))

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
            logger.error(f"Delete failed: {matched} \nReason: {e}\n")
        else:
            logger.info(Purple(f"Delete: {matched}"))
