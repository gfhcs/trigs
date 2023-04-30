import subprocess


def pacmd(*args):
    """
    Runs 'pacmd', which can control many aspects of PulsAudio.
    :param args: The arguments to be supplied to pacmd.
    :return: The output from pacmd.
    """
    return subprocess.run(["pacmd", *args], text=True, stdout=subprocess.PIPE).stdout


def pacmdlist():
    """
    Runs 'pacmd list'
    :return: A nest of dicts and lists.
    """

    level = 0

    path = [{}]

    lines = iter(pacmd("list").splitlines())

    for line in lines:
        print(line)
        l = line.replace("* index", "  index")
        level_new = len(l[:len(l) - len(l.lstrip())].replace("\t", "    ")) // 4
        sep = l.replace("=", ":").find(": ")

        if len(l.strip()) == 0:
            continue

        while level_new < level:
            path.pop(-1)
            level -= 1

        if sep == -1:
            if level == 0 and l.endswith("."):
                while len(path) > 1:
                    path.pop(-1)
                dd = []
            else:
                dd = {}
            path[-1][l] = dd
            path.append(dd)
            level += 1
        else:
            key, value = l[:sep].strip(), l[sep + 2:].strip()

            if key in ("volume", "channel map"):
                value += next(lines)

            if key == "index":
                while not isinstance(path[-1], list):
                    path.pop(-1)
                dd = {}
                path[-1].append(dd)
                path.append(dd)
            else:
                path[-1][key] = value

        level = level_new

    return path[0]

