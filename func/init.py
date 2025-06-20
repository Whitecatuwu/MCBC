from func.update import update
from func.ResPack import ResPack
from func.gui.ansi import Strong
from os import chdir, path as os_path
import configparser

PACK_PATH = "PackPath"
OPERATION_PATH = "OperationsPath"
OLDER_VERS = ["1.16.5", "1.16.1", "1.14.4", "1.12.2", "1.10.2", "1.8.9"]


def init(base_path: str) -> callable:

    config = configparser.ConfigParser()
    config.read("config.ini")
    __check_config(config)

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
            update(older_ver_res_packs[i - 1], older_ver_res_packs[i])

    def update_newer() -> None:
        for i in range(1, len(ver_res_packs), 1):
            print(Strong(f"{ver_res_packs[i].version():-^50}"))
            update(ver_res_packs[i - 1], ver_res_packs[i])

    return update_older, update_newer


def __check_config(config: configparser.ConfigParser) -> None:

    if not config.has_section(PACK_PATH):
        raise ValueError(f"Section '{PACK_PATH}' not found")
    if not config.has_section(OPERATION_PATH):
        raise ValueError(f"Section '{OPERATION_PATH}' not found")

    if not config.has_option(PACK_PATH, "core"):
        raise ValueError(f"Option 'core' not found in section '{PACK_PATH}' ")

    for ver in config.options(PACK_PATH):
        if ver == "core":
            continue
        if not config.has_option(OPERATION_PATH, ver):
            raise ValueError(f"Option '{ver}' not found in section '{OPERATION_PATH}' ")
