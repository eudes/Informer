from subprocess import run


def format_path(path):
    """
    Formatea un path de windows
    """
    return "\"" + path.replace("\\", "/") + "\""


def run_command(command):
    """
    Wrapper para los comandos de consola
    """
    return run(command, shell=True)
