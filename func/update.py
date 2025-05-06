from os import path as os_path
from .ansi import *
from .file_operation import copydata, delete
from .ResPack import ResPack


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
        copydata(
            src_update,
            dst_update,
            operations=None,
            mirror=mirror,
        )

    for (A,) in operations["A"]:
        src_update: str = os_path.join(ver.operations_path, os_path.basename(A))
        dst_update: str = os_path.join(dst, A)
        copydata(
            src_update,
            dst_update,
            operations=None,
            mirror=mirror,
        )
    for (D,) in operations["D"]:
        delete(os_path.join(dst, D))
