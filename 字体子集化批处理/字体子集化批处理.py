import tkinter as tk
from tkinter import filedialog
import ctypes
import sys
import os
import shlex
from datetime import datetime
import re

from loguru import logger



PROJECT_NAME = "字体子集化批处理"
PROJECT_VERSION = "0.1"
PROJECT_TITLE = f'{PROJECT_NAME} v{PROJECT_VERSION}'
PROJECT_URL = "https://github.com/op200/my_Gadgets"

MKVTOOL_VERSION = 'mkvtool-windows-amd64_v5.6.3'



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


if os.name == 'nt':
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


def run_subset(cmd: str):
    log.info(f'Run subset: {cmd}')
    if os.system(cmd):
        log.error(f'run_subset: run error')


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
            f"Used: MkvAutoSubset - mkvtool version: {MKVTOOL_VERSION}\n"
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


    elif cmd_list[0] in ('v', 'version'):
        print(f'{PROJECT_NAME} version {PROJECT_VERSION}\nUsed: MkvAutoSubset - mkvtool version: {MKVTOOL_VERSION}'
        f"")


    elif cmd_list[0][0] == "$":
        try:
            exec(' '.join(cmd_list)[1:].lstrip().replace(r"\N","\n"))
        except Exception as e:
            log.error("Your input command has error:")
            print(repr(e))


    elif cmd_list[0] == "exit":
        sys.exit()


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


    elif cmd_list[0] == 'fd':
        if fd_file_list := file_dialog():
            files = ' '.join(f'"{s.strip('"')}"' for s in fd_file_list)
            run_subset(f'{MKVTOOL_VERSION} s {files} -f 字体子集\\font -o 字体子集\\{datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")[:23]}')


    elif cmd_list[0] == 'all':
        file_dict: dict[str, list[str]] = dict()
        for f in [(re.match(r'(\d+)\.', s).group(1), s)
                  for s in os.listdir('.')
                  if os.path.isfile(s) and re.match(r'\d+\.zh-Han[st]', s)]:
            if f[0] in file_dict:
                file_dict[f[0]].append(f[1])
            else:
                file_dict[f[0]] = [f[1]]

        for k, v in file_dict.items():
            run_subset(f'{MKVTOOL_VERSION} s {' '.join('"'+f.strip('"')+'"' for f in v)} -f 字体子集\\font -o 字体子集\\{k}')


    elif re.match(r'\d+', cmd_list[0]):
        files = (f'{cmd_list[0]}.zh-Hans.ass', f'{cmd_list[0]}.zh-Hant.ass')
        for f in files:
            if not os.path.isfile(f):
                log.error(f'Can not exist the file {f}')
        run_subset(f'{MKVTOOL_VERSION} s "{files[0]}" "{files[1]}" -f 字体子集\\font -o 字体子集\\{cmd_list[0]}')


    elif os.path.isfile(cmd_list[0]):
        run_subset(f'{MKVTOOL_VERSION} s "{cmd_list[0]}" -f 字体子集\\font -o "字体子集\\{os.path.basename(cmd_list[0])}"')


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
        except:
            log.info("Manually force exit")
            sys.exit()

        try:
            cmd_list = [cmd.strip('"').strip("'").replace('\\\\', '\\')
                        for cmd in shlex.split(command, posix=False)]
        except ValueError as e:
            cmd_list = None
            log.error(e)
        if cmd_list == None or not run_command(cmd_list):
            log.warning('Stop run command')
