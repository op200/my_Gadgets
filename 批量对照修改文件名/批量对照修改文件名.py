import datetime
import tkinter as tk
from tkinter import filedialog
import ctypes
import sys
import os
import shlex
from pathlib import Path
import shutil
import subprocess
import platform
import json


PROJECT_NAME = "批量对照修改文件名"
PROJECT_VERSION = "0.2.1"
PROJECT_TITLE = f"{PROJECT_NAME} v{PROJECT_VERSION}"
PROJECT_URL = "https://github.com/op200/my_Gadgets"

RENAME_CACHE_FOLDER = (
    Path.home() / "AppData" / "Local" / "Temp" / f"{PROJECT_NAME}_rename_cache"
)

os.system(f"title {PROJECT_TITLE}")


class log:
    @staticmethod
    def info(msg: object):
        print(
            f"\033[32m{datetime.datetime.now().strftime('%Y.%m.%d %H:%M:%S.%f')[:-4]}\033[34m [INFO] {msg}\033[0m"
        )

    @staticmethod
    def warning(msg: object):
        print(
            f"\033[32m{datetime.datetime.now().strftime('%Y.%m.%d %H:%M:%S.%f')[:-4]}\033[33m [WARNING] {msg}\033[0m"
        )

    @staticmethod
    def error(msg: object):
        print(
            f"\033[32m{datetime.datetime.now().strftime('%Y.%m.%d %H:%M:%S.%f')[:-4]}\033[31m [ERROR] {msg}\033[0m"
        )


class config:
    config_dir: str
    config_file_pathname: str
    config_data: dict = {  # 默认参数
        "sec_suffix_list": []
    }

    @staticmethod
    def init():
        if platform.system() == "Windows":
            config.config_dir = os.path.join(os.getenv("APPDATA") or "", PROJECT_NAME)
        elif platform.system() == "Darwin":  # MacOS
            config.config_dir = os.path.join(
                os.path.expanduser("~"), "Library", "Application Support", PROJECT_NAME
            )
        else:  # Linux和其他类Unix系统
            config.config_dir = os.path.join(
                os.path.expanduser("~"), ".config", PROJECT_NAME
            )

        os.makedirs(config.config_dir, exist_ok=True)

        config.config_file_pathname = os.path.join(config.config_dir, "config.json")

        if not os.path.exists(config.config_file_pathname):
            config.write_config()

        with open(config.config_file_pathname, "rt", encoding="utf-8") as config_file:
            config.config_data = json.load(config_file)

    @staticmethod
    def flush_config_data():
        config.config_data["sec_suffix_list"] = runner.sec_suffix_list

    @staticmethod
    def write_config():
        with open(config.config_file_pathname, "wt", encoding="utf-8") as config_file:
            json.dump(config.config_data, config_file, indent=2)


config.init()


class runner:
    list_1: list[Path] = []
    list_2: list[str] = []
    ratio: int = 1
    sec_suffix_list: list[str] = config.config_data.get("sec_suffix_list", [])

    @staticmethod
    def rm_cache():
        shutil.rmtree(RENAME_CACHE_FOLDER, ignore_errors=True)

    @staticmethod
    def exit():
        runner.rm_cache()
        config.flush_config_data()
        config.write_config()
        sys.exit()

    @staticmethod
    def get_list_2(i: int):
        try:
            return runner.list_2[i]
        except IndexError:
            return ""

    @staticmethod
    def get_suffix(i: int):
        try:
            return runner.sec_suffix_list[i]
        except IndexError:
            return f".{i + 1}"

    @staticmethod
    def add_list_1(str_list: tuple[str, ...]):
        runner.list_1.extend(Path(v) for v in str_list)

    @staticmethod
    def add_list_2(str_list: tuple[str, ...]):
        runner.list_2.extend((os.path.basename(v) for v in str_list))

    @staticmethod
    def add_sec_suffix(sec_suffix: str):
        if sec_suffix[0] != ".":
            runner.sec_suffix_list.append(f".{sec_suffix}")
        else:
            runner.sec_suffix_list.append(sec_suffix)

    @staticmethod
    def sort_list():
        runner.list_1.sort(key=lambda x: x.name)
        runner.list_2.sort()

    @staticmethod
    def get_res_list():
        res_list: list[tuple[Path, str]] = []
        for i, path in enumerate(runner.list_1):
            basename = os.path.splitext(
                os.path.basename(runner.get_list_2(i // runner.ratio))
            )[0]
            sec_suffix = runner.get_suffix(i % runner.ratio)
            suffix = os.path.splitext(os.path.basename(path.as_posix()))[1]
            res_list.append(
                (path, "" if basename == "" else basename + sec_suffix + suffix)
            )

        return res_list

    @staticmethod
    def run(is_exit: bool):
        runner.sort_list()

        runner.rm_cache()
        os.makedirs(RENAME_CACHE_FOLDER, exist_ok=True)

        res_list = runner.get_res_list()
        empty_indices = [i + 1 for i, v in enumerate(res_list) if v[1] == ""]
        if empty_indices:
            log.error(
                f"The ({', '.join(map(str, empty_indices))})th in list_2 is empty"
            )
            return

        for v in res_list:
            if v[0].stat().st_size > 20971520:  # 20MB
                log.error(f"The file {v[0].as_posix()} is too large (file > 20 MB)")
                return
            shutil.copy(v[0], Path(os.path.join(RENAME_CACHE_FOLDER, v[1])))

        openfolder = subprocess.Popen(["start", RENAME_CACHE_FOLDER], shell=True)
        openfolder.wait()

        if is_exit:
            runner.exit()


try:
    ctypes.windll.user32.SetProcessDPIAware()
except:  # noqa: E722
    log.warning("Windows DPI Aware failed")


def file_dialog() -> tuple[str, ...]:
    tkRoot = tk.Tk()
    tkRoot.withdraw()
    file_paths = filedialog.askopenfilenames() or tuple()
    tkRoot.destroy()
    return file_paths


def get_input_prompt():
    return f"{os.getcwd()}> Add command>"


def run_command(cmd_list: list[str] | str) -> bool:
    if isinstance(cmd_list, str):
        cmd_list = [cmd_list]

    if len(cmd_list) == 0:
        return True

    os.system(f"title {PROJECT_TITLE}")

    cmd_list.append("")

    match cmd_list[0]:
        case "h" | "help":
            print(
                f"{PROJECT_NAME}\nVersion: {PROJECT_VERSION}\n{PROJECT_URL}\n"
                "\n"
                "Help:\n"
                "  You can input command or use the argument value to run\n"
                "\n"
                "\n"
                "Commands:\n"
                "  h / help\n"
                "    Show help\n"
                "\n"
                "  v / version\n"
                "    Show version\n"
                "\n"
                "  $ <code>\n"
                "    Run code directly from the internal environment\n"
                "    Execute the code string directly after the $\n"
                '    The string "\\N" will be changed to real "\\n"\n'
                "\n"
                "  exit\n"
                "    Save config, delete cache, exit this program\n"
                "\n"
                "  cd <string>\n"
                "    Change current path\n"
                "\n"
                "  cls / clear\n"
                "    Clear screen\n"
                "\n"
                "  open <string>\n"
                "    Open folder\n"
                "    conf / config / appdata:\n"
                "      Open the config folder\n"
                "    tmp / temp / temporary:\n"
                "      Open the temp folder\n"
                "\n"
                "  add <string>\n"
                "    Add something to rename\n"
                "    1:\n"
                "      Add renamed files\n"
                "    2:\n"
                "      Add reference files\n"
                "    s / suf / suffix:\n"
                "      Add second suffix\n"
                "\n"
                "  add1\n"
                "    Same to add 1\n"
                "\n"
                "  add2\n"
                "    Same to add 2\n"
                "\n"
                "  adds / addsuf / addsuffix\n"
                "    Same to add suffix\n"
                "\n"
                "  r / ratio / k <int>\n"
                "    Set the ratio of 'add1 : add2'\n"
                "    Default: 1\n"
                "\n"
                "  list <list option>\n"
                "    Operate list\n"
                "    Default:\n"
                "      Show list\n"
                "    clear / clean:\n"
                "      Clear list\n"
                "    del1 / pop1 <index>:\n"
                "      Delete a member from list_1\n"
                "    del2 / pop2 <index>:\n"
                "      Delete a member from list_2\n"
                "\n"
                "  run [<run option>]\n"
                "    Run renamer\n"
                "    Default:\n"
                "      Only run\n"
                "    exit:\n"
                "      Close program when runned\n"
            )

        case "v" | "ver" | "version":
            print(f"{PROJECT_NAME} version {PROJECT_VERSION}")

        case str() as s if len(s) > 0 and s[0] == "$":
            try:
                exec(" ".join(cmd_list)[1:].lstrip().replace(r"\N", "\n"))
            except Exception as e:
                log.error("Your input command has error:")
                print(repr(e))

        case "exit":
            runner.exit()

        case "cd":
            try:
                os.chdir(cmd_list[1])
            except OSError as e:
                log.error(e)

        case "cls" | "clear":
            if os.name == "nt":
                os.system("cls")
            else:
                os.system("clear")

        case "open":
            if cmd_list[1] in ("conf", "config", "appdata"):
                openfolder = subprocess.Popen(["start", config.config_dir], shell=True)
                openfolder.wait()
            elif cmd_list[1] in ("tmp", "temp", "temporary"):
                openfolder = subprocess.Popen(
                    ["start", RENAME_CACHE_FOLDER], shell=True
                )
                openfolder.wait()

        case "add":
            if cmd_list[1] == "1":
                runner.add_list_1(file_dialog())
            elif cmd_list[1] == "2":
                runner.add_list_2(file_dialog())
            elif cmd_list[1] in ("s", "suf", "suffix"):
                runner.add_sec_suffix(cmd_list[2])

        case "add1":
            runner.add_list_1(file_dialog())
        case "add2":
            runner.add_list_2(file_dialog())
        case "adds" | "addsuf" | "addsuffix":
            runner.add_sec_suffix(cmd_list[1])

        case "r" | "ratio" | "k":
            try:
                runner.ratio = int(cmd_list[1])
            except ValueError:
                log.error(f'Error value in set ratio command: "{cmd_list[1]}"')

        case "list":
            match cmd_list[1]:
                case "clear" | "clean":
                    if cmd_list[2] == "1":
                        runner.list_1 = []
                    elif cmd_list[2] == "2":
                        runner.list_2 = []
                    elif cmd_list[2] in ("s", "suf", "suffix"):
                        runner.sec_suffix_list = []
                    else:
                        runner.list_1 = []
                        runner.list_2 = []

                case "del1" | "pop1":
                    try:
                        del runner.list_1[int(cmd_list[2]) - 1]
                    except Exception as e:
                        log.error(e)
                    else:
                        log.info(f"Delete the {cmd_list[2]}th success")

                case "del2" | "pop2":
                    try:
                        del runner.list_2[int(cmd_list[2]) - 1]
                    except Exception as e:
                        log.error(e)
                    else:
                        log.info(f"Delete the {cmd_list[2]}th success")

                case _:
                    runner.sort_list()
                    res_list = runner.get_res_list()

                    print(f"second suffix list ({len(runner.sec_suffix_list)}):")
                    for i, v in enumerate(runner.sec_suffix_list):
                        print(f"  {i + 1:>3}. {v}")

                    print(f"list ({len(res_list)}) ratio {runner.ratio}:")
                    for i, v in enumerate(res_list):
                        print(f"  {i + 1:>3}. {v[0].as_posix()}\n         ->{v[1]}")

        case "run":
            runner.run(cmd_list[1] == "exit")

        case _:
            log.error(f'Unknow command: "{cmd_list}"')
            return False

    return True


if __name__ == "__main__":
    runner.list_1 = []
    runner.list_2 = []
    runner.ratio = 1

    if sys.argv[1:] != []:
        run_command(sys.argv[1:])

    while True:
        try:
            command = input(get_input_prompt())
        except:  # noqa: E722
            log.info("Manually force exit")
            runner.exit()

        try:
            cmd_list = [
                cmd.strip('"').strip("'").replace("\\\\", "\\")
                for cmd in shlex.split(command, posix=False)  # type: ignore
            ]
        except ValueError as e:
            cmd_list = None
            log.error(e)
        if cmd_list is None or not run_command(cmd_list):
            log.warning("Stop run command")
