from src.PackUpdate import PackUpdate
from src.ResPack import ResPack
from src.gui.ansi import Strong
from os import path as os_path
from src.config import PACK_PATH, OPERATION_PATH, read_config


OLDER_VERS = ["1.16.5", "1.16.1", "1.14.4", "1.12.2", "1.10.2", "1.8.9"]


def init(base_path: str) -> callable:

    config = read_config()

    versions: list[str] = config.options(OPERATION_PATH)

    core_pack_path: str = config.get(PACK_PATH, "core")
    core_res_pack: ResPack = ResPack(os_path.join(base_path, core_pack_path), "core")

    ver_res_packs: list[ResPack] = [core_res_pack]
    older_ver_res_packs: list[ResPack] = [core_res_pack]

    for ver in versions:
        res_pack_path: str = os_path.join(base_path, config.get(PACK_PATH, ver))
        operations_path: str = os_path.join(base_path, config.get(OPERATION_PATH, ver))
        pack: ResPack = ResPack(res_pack_path, ver, operations_path)
        if ver not in OLDER_VERS:
            ver_res_packs.append(pack)

    for ver in OLDER_VERS:
        res_pack_path: str = os_path.join(base_path, config.get(PACK_PATH, ver))
        operations_path: str = os_path.join(base_path, config.get(OPERATION_PATH, ver))
        pack: ResPack = ResPack(res_pack_path, ver, operations_path)
        older_ver_res_packs.append(pack)

    def update_older() -> None:
        for i in range(1, len(older_ver_res_packs), 1):
            print(Strong(f"{older_ver_res_packs[i].version():-^50}"))
            PackUpdate(older_ver_res_packs[i - 1], older_ver_res_packs[i]).update()

    def update_newer() -> None:
        for i in range(1, len(ver_res_packs), 1):
            print(Strong(f"{ver_res_packs[i].version():-^50}"))
            PackUpdate(ver_res_packs[i - 1], ver_res_packs[i]).update()

    return update_older, update_newer
