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

from loguru import logger



PROJECT_NAME = "批量对照修改文件名"
PROJECT_VERSION = "0.1"
PROJECT_TITLE = f'{PROJECT_NAME} v{PROJECT_VERSION}'
PROJECT_URL = "https://github.com/op200"

RENAME_CACHE_FOLDER = Path.home() / 'AppData' / 'Local' / 'Temp' / f'{PROJECT_NAME}_rename_cache'

os.system(f'title {PROJECT_TITLE}')



logger.remove()
logger.add(sys.stderr, format="<green>{time:YYYY.MM.DD HH:mm:ss.SS}</green><blue><level> [{level}] {message}</level></blue>")

class log:

    @staticmethod
    def info( __message: str, *args, **kwargs):
        logger.info(__message, *args, **kwargs)

    @staticmethod
    def warning( __message: str, *args, **kwargs):
        logger.warning(__message, *args, **kwargs)

    @staticmethod
    def error( __message: str, *args, **kwargs):
        logger.error(__message, *args, **kwargs)



class config:

    config_dir: str
    config_file_pathname: str
    config_data: dict = { # 默认参数
        'sec_suffix_list': []
    }


    def init():
        if platform.system() == "Windows":
            config.config_dir = os.path.join(os.getenv('APPDATA'), PROJECT_NAME)
        elif platform.system() == "Darwin":  # MacOS
            config.config_dir = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', PROJECT_NAME)
        else:  # Linux和其他类Unix系统
            config.config_dir = os.path.join(os.path.expanduser('~'), '.config', PROJECT_NAME)

        os.makedirs(config.config_dir, exist_ok=True)

        config.config_file_pathname = os.path.join(config.config_dir, 'config.json')

        if not os.path.exists(config.config_file_pathname):
            config.write_config()

        with open(config.config_file_pathname, 'rt', encoding='utf-8') as config_file:
            config.config_data = json.load(config_file)


    def flush_config_data():
        config.config_data['sec_suffix_list'] = runner.sec_suffix_list


    def write_config():
        with open(config.config_file_pathname, 'wt', encoding='utf-8') as config_file:
            json.dump(config.config_data, config_file, indent=2)


config.init()



class runner:

    list_1: list[Path] = []
    list_2: list[str] = []
    ratio: int = 1
    sec_suffix_list: list[str] = config.config_data.get('sec_suffix_list') or []

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
            return ''

    @staticmethod
    def get_suffix(i: int):
        try:
            return runner.sec_suffix_list[i]
        except IndexError:
            return f'.{i+1}'

    @staticmethod
    def add_list_1(str_list: list[str]):
        for v in str_list:
            runner.list_1.append(Path(v))

    @staticmethod
    def add_list_2(str_list: list[str]):
        runner.list_2.extend((os.path.basename(v) for v in str_list))

    @staticmethod
    def add_sec_suffix(sec_suffix: str):
        if sec_suffix[0] != '.':
            runner.sec_suffix_list.append(f'.{sec_suffix}')
        else:
            runner.sec_suffix_list.append(sec_suffix)

    @staticmethod
    def sort_list():
        runner.list_1.sort(key = lambda x: x.name)
        runner.list_2.sort()

    @staticmethod
    def get_res_list():
        res_list: list[tuple[Path, str]] = []
        for i, path in enumerate(runner.list_1):
            basename = os.path.splitext(os.path.basename(runner.get_list_2(i // runner.ratio)))[0]
            sec_suffix = runner.get_suffix(i % runner.ratio)
            suffix = os.path.splitext(os.path.basename(path.as_posix()))[1]
            res_list.append((path,
                             '' if basename == '' else basename + sec_suffix + suffix))

        return res_list

    @staticmethod
    def run(is_exit: bool):

        runner.sort_list()

        runner.rm_cache()
        os.makedirs(RENAME_CACHE_FOLDER, exist_ok=True)

        res_list = runner.get_res_list()
        if '' in res_list:
            log.error(f'The ({', '.join(str(i+1) for i, v in enumerate(res_list) if v[1] == '')})th in list_2 is empty')
            return

        for v in res_list:
            if v[0].stat().st_size > 20971520: # 20MB
                log.error(f'The file {v[0].as_posix()} is too large (file > 20 MB)')
                return
            shutil.copy(v[0], Path(os.path.join(RENAME_CACHE_FOLDER, v[1])))

        openfolder = subprocess.Popen(['start', RENAME_CACHE_FOLDER], shell=True)
        openfolder.wait()

        if is_exit:
            runner.exit()

try:
    ctypes.windll.user32.SetProcessDPIAware()
except:
    log.warning("Windows DPI Aware failed")


def file_dialog():
    tkRoot = tk.Tk()
    tkRoot.withdraw()
    file_paths = filedialog.askopenfilenames()
    tkRoot.destroy()
    return file_paths


def get_input_prompt():
    return f'{os.getcwd()}> Add command>'


def run_command(cmd_list: list[str] | str) -> bool:

    if type(cmd_list) is str:
        cmd_list = [cmd_list]

    if len(cmd_list) == 0:
        return True

    os.system(f'title {PROJECT_TITLE}')

    cmd_list.append('')

    if cmd_list[0] in ('h', 'help'):

        print(
            f"{PROJECT_NAME}\nVersion: {PROJECT_VERSION}\n{PROJECT_URL}\n"
            "\n"
            "Help:\n"
            "  You can input command or use the argument value to run\n"
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
            "    Save config, delete cache, exit this program\n"
            "  cd <string>\n"
            "    Change current path\n"
            "  cls / clear\n"
            "    Clear screen\n"

            "  open <string>\n"
            "    Open folder\n"
            "    conf / config / appdata:\n"
            "      Open the config folder\n"
            "    tmp / temp / temporary:\n"
            "      Open the temp folder\n"

            "  add <string>\n"
            "    Add something to rename\n"
            "    1:\n"
            "      Add renamed files\n"
            "    2:\n"
            "      Add reference files\n"
            "    s / suf / suffix:\n"
            "      Add second suffix\n"
            "  add1\n"
            "    Same to add 1\n"
            "  add2\n"
            "    Same to add 2\n"
            "  adds / addsuf / addsuffix\n"
            "    Same to add suffix\n"

            "  r / ratio / k <int>\n"
            "    Set the ratio of 'add1 : add2'\n"
            "    Default: 1\n"

            "  list <list option>\n"
            "    Operate ripper list\n"
            "    Default:\n"
            "      Show ripper list\n"
            "    clear / clean:\n"
            "      Clear ripper list\n"
            "    del1 / pop1 <index>:\n"
            "      Delete a member from list_1\n"
            "    del2 / pop2 <index>:\n"
            "      Delete a member from list_2\n"
            "  run [<run option>]\n"
            "    Run renamer\n"
            "    Default:\n"
            "      Only run\n"
            "    exit:\n"
            "      Close program when runned\n"
        )


    elif cmd_list[0] in ('v', 'version'):
        print(f'{PROJECT_NAME} version {PROJECT_VERSION}')


    elif cmd_list[0][0] == "$":
        try:
            exec(' '.join(cmd_list)[1:].lstrip().replace(r"\N","\n"))
        except Exception as e:
            log.error("Your input command has error:")
            print(repr(e))


    elif cmd_list[0] == "exit":
        runner.exit()


    elif cmd_list[0] == "cd":
        try:
            os.chdir(cmd_list[1])
        except OSError as e:
            log.error(e)


    elif cmd_list[0] in ('cls', 'clear') and cmd_list[1] == '':
        if os.name == 'nt':
            os.system('cls')
        else:
            os.system('clear')


    elif cmd_list[0] == 'open':
        if cmd_list[1] in ('conf','config', 'appdata'):
            openfolder = subprocess.Popen(['start', config.config_dir], shell=True)
            openfolder.wait()
        elif cmd_list[1] in ('tmp','temp', 'temporary'):
            openfolder = subprocess.Popen(['start', RENAME_CACHE_FOLDER], shell=True)
            openfolder.wait()


    elif cmd_list[0] == 'add':
        if cmd_list[1] == '1':
            runner.add_list_1(file_dialog())
        elif cmd_list[1] == '2':
            runner.add_list_2(file_dialog())
        elif cmd_list[1] in ('s', 'suf', 'suffix'):
            runner.add_sec_suffix(cmd_list[2])


    elif cmd_list[0] == 'add1':
        runner.add_list_1(file_dialog())
    elif cmd_list[0] == 'add2':
        runner.add_list_2(file_dialog())
    elif cmd_list[0] in ('adds', 'addsuf', 'addsuffix'):
        runner.add_sec_suffix(cmd_list[1])


    elif cmd_list[0] in ('r', 'ratio', 'k'):
        try:
            runner.ratio = int(cmd_list[1])
        except ValueError:
            log.error(f'Error value in set ratio command: "{cmd_list[1]}"')


    elif cmd_list[0] == "list":

        if cmd_list[1] in ('clear', 'clean'):
            if cmd_list[2] == '1':
                runner.list_1 = []
            elif cmd_list[2] == '2':
                runner.list_2 = []
            elif cmd_list[2] in ('s', 'suf', 'suffix'):
                runner.sec_suffix_list = []
            else:
                runner.list_1 = []
                runner.list_2 = []

        elif cmd_list[1] in ('del1', 'pop1'):
            try:
                del runner.list_1[int(cmd_list[2])-1]
            except Exception as e:
                log.error(e)
            else:
                log.info(f'Delete the {cmd_list[2]}th ripper success')

        elif cmd_list[1] in ('del2', 'pop2'):
            try:
                del runner.list_2[int(cmd_list[2])-1]
            except Exception as e:
                log.error(e)
            else:
                log.info(f'Delete the {cmd_list[2]}th ripper success')

        else:
            runner.sort_list()
            res_list = runner.get_res_list()

            print(f'second suffix list ({len(runner.sec_suffix_list)}):')
            for i, v in enumerate(runner.sec_suffix_list):
                print(f'  {i+1:>3}. {v}')

            print(f'list ({len(res_list)}) ratio {runner.ratio}:')
            for i, v in enumerate(res_list):
                print(f'  {i+1:>3}. {v[0].as_posix()}\n         ->{v[1]}')


    elif cmd_list[0] == "run":
        runner.run(cmd_list[1] == 'exit')


    else:

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
        except:
            log.info("Manually force exit")
            runner.exit()

        try:
            cmd_list = [cmd.strip('"').strip("'").replace('\\\\', '\\')
                        for cmd in shlex.split(command, posix=False)]
        except ValueError as e:
            cmd_list = None
            log.error(e)
        if cmd_list == None or not run_command(cmd_list):
            log.warning('Stop run command')
