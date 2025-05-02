from func.update import *
from time import time as current_time
from os import chdir

CURRENT_DIR = os_path.dirname(os_path.abspath(__file__))


def main():
    older_vers = ["", "1.16.5", "1.16.1", "1.14.4", "1.12.2", "1.10.2", "1.8.9"]
    vers = [
        "",
        "1.17.1",
        "1.18.2",
        "1.19.2",
        "1.19.3",
        "1.19.4",
        "1.20.1",
        "1.20.2",
        "1.20.4",
        "1.20.6",
        "1.21.1",
        "1.21.3",
        "1.21.4",
        "1.21.5",
    ]

    ver_res_packs = []
    for ver in vers:
        if ver == "":
            pack = ResPack(os_path.join(CURRENT_DIR, "battlecats"), ver)
        else:
            pack = ResPack(
                os_path.join(CURRENT_DIR, "battlecats_" + ver),
                ver,
                os_path.join(CURRENT_DIR, "battlecats", "vers", ver),
            )
        ver_res_packs.append(pack)

    older_ver_res_packs = []
    for old in older_vers:
        if old == "":
            pack = ResPack(os_path.join(CURRENT_DIR, "battlecats"), old)
        else:
            pack = ResPack(
                os_path.join(CURRENT_DIR, "battlecats_" + old),
                old,
                os_path.join(CURRENT_DIR, "battlecats", "vers", old),
            )
        older_ver_res_packs.append(pack)

    def update_older() -> None:
        for i in range(1, len(older_ver_res_packs), 1):
            print(Strong(f"{older_ver_res_packs[i].version():-^50}"))
            update(older_ver_res_packs[i - 1], older_ver_res_packs[i])

    def update_newer() -> None:
        for i in range(1, len(ver_res_packs), 1):
            print(Strong(f"{ver_res_packs[i].version():-^50}"))
            update(ver_res_packs[i - 1], ver_res_packs[i])

    update_older()
    update_newer()


if __name__ == "__main__":

    chdir(CURRENT_DIR)
    while True:
        start_time = current_time()
        main()
        print("\nFinish.")
        print("runtime: %s seconds" % (current_time() - start_time))
        c = input("Press Enter to continue or -1 to exit...\n")
        if c == "-1":
            break
