from src.config import PACK_PATH, OPERATION_PATH, read_config
from src.file_operation import delete
from os import scandir, path as os_path


BASE_PATH = os_path.dirname(os_path.abspath(__file__))

if __name__ == "__main__":
    config = read_config()
    versions: list[str] = config.options(OPERATION_PATH)
    for ver in versions:
        res_pack_path: str = os_path.join(BASE_PATH, config.get(PACK_PATH, ver))
        res_pack_path = os_path.normpath(res_pack_path)
        asset_path: str = os_path.join(res_pack_path, "assets")
        for x in scandir(asset_path):
            delete(os_path.join(asset_path, x.name))
