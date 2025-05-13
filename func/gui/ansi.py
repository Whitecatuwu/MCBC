def Grey(skk):
    return "\033[90m{}\033[00m".format(skk)  # ignore


def Red(skk):
    return "\033[91m{}\033[00m".format(skk)  # error


def Green(skk):
    return "\033[92m{}\033[00m".format(skk)  # update


def Yellow(skk):
    return "\033[93m{}\033[00m".format(skk)  # warning


def Blue(skk):
    return "\033[94m{}\033[00m".format(skk)  # keep


def Purple(skk):
    return "\033[95m{}\033[00m".format(skk)  # delete


def Cyan(skk):
    return "\033[96m{}\033[00m".format(skk)  # skip


def White(skk):
    return "\033[97m{}\033[00m".format(skk)


def Orange(skk):
    return "\033[38;5;214m{}\033[00m".format(skk)  # rename


def Strong(skk):
    return "\033[1m{}\033[0m".format(skk)
