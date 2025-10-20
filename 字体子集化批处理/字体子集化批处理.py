import ctypes
import json
import os
import re
import shlex
import sys
import tkinter as tk
from datetime import datetime
from tkinter import filedialog

from loguru import logger

PROJECT_NAME = "字体子集化批处理"
PROJECT_VERSION = "0.2.1"
PROJECT_TITLE = f"{PROJECT_NAME} v{PROJECT_VERSION}"
PROJECT_URL = "https://github.com/op200/my_Gadgets"


CONFIG_NAME = "字体子集化批处理_config.json"

config: dict = {
    "mkvtool_name": "mkvtool-windows-amd64_v5.6.4",
    "subfont_path": "字体子集",
    "subfont_path_fonts_path": "font",
    "abs_fonts_path": None,
}

if os.path.exists(CONFIG_NAME):
    with open(CONFIG_NAME, "rt", encoding="utf-8") as f:
        conf: dict = json.load(f)
        for key in config.keys():
            if val := conf.get(key):
                config[key] = val


os.system(f"title {PROJECT_TITLE}")


logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY.MM.DD HH:mm:ss.SS}</green><blue><level> [{level}] {message}</level></blue>",
)


class log:
    @staticmethod
    def info(__message: str, *args, **kwargs):
        logger.info(__message, *args, **kwargs)

    @staticmethod
    def warning(__message: str, *args, **kwargs):
        logger.warning(__message, *args, **kwargs)

    @staticmethod
    def error(__message: str, *args, **kwargs):
        logger.error(__message, *args, **kwargs)


log.warning("This is an abandoned project. 这是一个已弃用的项目。")

if os.name == "nt":
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        log.warning("Windows DPI Aware failed")


def file_dialog():
    tkRoot = tk.Tk()
    tkRoot.withdraw()
    file_paths = filedialog.askopenfilenames()
    tkRoot.destroy()
    return file_paths


def get_input_prompt():
    return f"{os.getcwd()}> Add command>"


def run_subset(cmd: str):
    log.info(f"Run subset: {cmd}")
    if os.system(cmd):
        log.error("run_subset: run error")


def run_command(cmd_list: list[str] | str) -> bool:
    if isinstance(cmd_list, str):
        cmd_list = [cmd_list]

    if len(cmd_list) == 0:
        return True

    os.system(f"title {PROJECT_TITLE}")

    cmd_list.append("")

    if cmd_list[0] in ("h", "help"):
        print(
            f"{PROJECT_NAME}\nVersion: {PROJECT_VERSION}\n{PROJECT_URL}\n"
            f"Used: MkvAutoSubset - mkvtool version: {config['mkvtool_name']}\n"
            "\n"
            "Help:\n"
            "  You can input command to do something about run subset or input something from cmd\n"
            "\n"
            "Commands:\n"
            "  h / help\n"
            "    Show help\n"
            "  v / version\n"
            "    Show version\n"
            "  $ <code>\n"
            "    Run code directly from the internal environment\n"
            "    Execute the code string directly after the $\n"
            '    The string "\\N" will be changed to real "\\n"\n'
            "  exit\n"
            "    Exit this program\n"
            "  cd <string>\n"
            "    Change current path\n"
            "  cls / clear\n"
            "    Clear screen\n"
            "  <run>\n"
            "    File pathname or ep number or file dialog\n"
            "    Pathname:\n"
            "      One string e.g. E:/subtitles/01.ass\n"
            "    Ep number:\n"
            "      Input an 'ep', the 'ep'.zh-Hans.ass and 'ep'.zh-Hant.ass will be subsetted\n"
            "      e.g. input '01', the 01.zh-Hans.ass and 01.zh-Hant.ass will be subsetted\n"
            "    File dialog:\n"
            "      Input 'fd' to use file dialog\n"
            "    All ep:\n"
            "      Input 'all' to subset all 'ep'.zh-Hans.ass and 'ep'.zh-Hant.ass in the current directory\n"
            "      i.e. \\d+\\.zh-Han[st]\\.ass\n"
        )

    elif cmd_list[0] in ("v", "version"):
        print(
            f"{PROJECT_NAME} version {PROJECT_VERSION}\nUsed: MkvAutoSubset - mkvtool version: {config['mkvtool_name']}"
            f""
        )

    elif cmd_list[0][0] == "$":
        try:
            exec(" ".join(cmd_list)[1:].lstrip().replace(r"\N", "\n"))
        except Exception as e:
            log.error("Your input command has error:")
            print(repr(e))

    elif cmd_list[0] == "exit":
        sys.exit()

    elif cmd_list[0] == "cd":
        try:
            os.chdir(cmd_list[1])
        except OSError as e:
            log.error(str(e))

    elif cmd_list[0] in ("cls", "clear") and cmd_list[1] == "":
        if os.name == "nt":
            os.system("cls")
        else:
            os.system("clear")

    elif cmd_list[0] == "fd":
        if fd_file_list := file_dialog():
            files = " ".join(f'"{s.strip('"')}"' for s in fd_file_list)
            run_subset(
                f"{config['mkvtool_name']} s {files} -f {config['abs_fonts_path'] or f'{config["subfont_path"]}\\{config["subfont_path_fonts_path"]}'} -o {config['subfont_path']}\\{datetime.now().strftime('%Y-%m-%d_%H-%M-%S_%f')[:23]}"
            )

    elif cmd_list[0] == "all":
        file_dict: dict[str, list[str]] = dict()
        for f in [
            (re.match(r"(\d+)\.", s), s)
            for s in os.listdir(".")
            if os.path.isfile(s) and re.match(r"\d+\.zh-Han[st]", s)
        ]:
            if f[0] is None:
                continue
            if f[0] in file_dict:
                file_dict[f[0].group(1)].append(f[1])
            else:
                file_dict[f[0].group(1)] = [f[1]]

        for k, v in file_dict.items():
            run_subset(
                f"{config['mkvtool_name']} s {' '.join('"' + f.strip('"') + '"' for f in v)} -f {config['abs_fonts_path'] or f'{config["subfont_path"]}\\{config["subfont_path_fonts_path"]}'} -o {config['subfont_path']}\\{k}"
            )

    elif re.match(r"\d+", cmd_list[0]):
        files = (f"{cmd_list[0]}.zh-Hans.ass", f"{cmd_list[0]}.zh-Hant.ass")
        for f in files:
            if not os.path.isfile(f):
                log.error(f"Can not exist the file {f}")
        run_subset(
            f'{config["mkvtool_name"]} s "{files[0]}" "{files[1]}" -f {config["abs_fonts_path"] or f"{config['subfont_path']}\\{config['subfont_path_fonts_path']}"} -o {config["subfont_path"]}\\{cmd_list[0]}'
        )

    elif os.path.isfile(cmd_list[0]):
        run_subset(
            f'{config["mkvtool_name"]} s "{cmd_list[0]}" -f {config["abs_fonts_path"] or f"{config['subfont_path']}\\{config['subfont_path_fonts_path']}"} -o "{config["subfont_path"]}\\{os.path.basename(cmd_list[0])}"'
        )

    else:
        log.error(f'Unknow command: "{cmd_list}"')
        return False

    return True


if __name__ == "__main__":
    if sys.argv[1:] != []:
        run_command(sys.argv[1:])
        sys.exit()

    while True:
        try:
            command = input(get_input_prompt())
        except Exception:
            log.info("Manually force exit")
            sys.exit()

        try:
            cmd_list = [
                cmd.strip('"').strip("'").replace("\\\\", "\\")
                for cmd in shlex.split(command, posix=False)
            ]
        except ValueError as e:
            cmd_list = None
            log.error(str(e))
        if cmd_list is None or not run_command(cmd_list):
            log.warning("Stop run command")
