import configparser

PACK_PATH = "PackPath"
OPERATION_PATH = "OperationsPath"


def read_config() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config.read("config.ini")
    __check_config(config)
    return config


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
