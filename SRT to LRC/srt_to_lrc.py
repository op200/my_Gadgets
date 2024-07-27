import re
import sys
import os


PROGRAM_NAME = "srt_to_lrc"
VERSION = "0.1"
HOME_LINK = "https://github.com/op200/my_Gadgets"


def srt_to_lrc(srt_file, lrc_file):
    # 正则表达式匹配SRT文件的时间戳格式
    time_pattern = re.compile(r'(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2}):(\d{2}):(\d{2}),(\d{3})')
    
    with open(srt_file, 'r', encoding='utf-8') as srt, open(lrc_file, 'w', encoding='utf-8') as lrc:
        for line in srt:
            line = line.strip()
            if not line:
                continue

            # 检查是否是时间戳行
            match = time_pattern.match(line)
            if match:
                # 解析时间戳
                h1, m1, s1, ms1, h2, m2, s2, ms2 = match.groups()
                
                # 转换为LRC时间戳格式（分钟:秒.毫秒）
                start_time = f"[{int(m1):02}:{int(s1):02}.{int(ms1) // 10:02}]"
                # end_time = f"[{int(m2):02}:{int(s2):02}.{int(ms2) // 10:02}]"

                # 读取下一个行，作为字幕文本
                subtitle_text = next(srt).strip()
                if subtitle_text:
                    # 写入LRC文件
                    lrc.write(f"{start_time}{subtitle_text}\n")
                    
                continue


#日志
class log:
    log_level = 0

    @staticmethod
    def output(info:object):
        print(info)

    @staticmethod
    def exit():
        log.error("program interruption")
        exit()

    @staticmethod
    def error(info:object, level:int=110):
        if level>log.log_level:
            log.output(f"\033[31m[ERROR]\033[0m {info}")

    @staticmethod
    def errore(info:object):
        log.error(info)
        log.exit()

    @staticmethod
    def warning(info:object, level:int=70):
        if level>log.log_level:
            log.output(f"\033[33m[WARNING]\033[0m {info}")

    @staticmethod
    def info(info:object, level:int=30):
        if level>log.log_level:
            log.output(f"\033[35m[INFO]\033[0m {info}")



input_path:str = None
output_path:str = None
overwrite_lrc:bool = False

cmds = sys.argv[1:]

for cmd in cmds:
    if cmd=="-v" or cmd=="-version":
        log.output(f"{PROGRAM_NAME}\nVersion: {VERSION}\n{HOME_LINK}")
        exit()
    if cmd=="-h" or cmd=="-help":
        print(f"""
{PROGRAM_NAME} help:

-h/-help
    print help

-v/-version
    print version

-i/-input <string>
    the input path of a video or img sequence
    default: {input_path}

-o/-output <string>
    the output path of txt
    default: {output_path}

-ow <bool>
    is it overwrite txt
    default: {overwrite_lrc}

-loglevel <int>
    log level
    if it > 20 , some INFO    will not be print
    if it > 40 , all  INFO    will not be print
    if it > 60 , some WARRING will not be print
    if it > 80 , all  WARRING will not be print
    if it > 100, some ERROR   will not be print
    if it > 120, all  ERROR   will not be print
    if it > 140, all  logs    will not be print
    default: 0
        """)
        exit()

for i in range(len(cmds)):
    # input
    if cmds[i]=="-i" or cmds[i]=="-input":
        input_path = cmds[i+1]

    # output
    if cmds[i]=="-o" or cmds[i]=="-output":
        output_path = cmds[i+1]


if not input_path:
    log.errore("Missing input file")
if not output_path:
    log.errore("Missing output file")

if output_path[-4:] != ".lrc":
    log.warning("The suffix of the output file is not '.lrc' and has been automatically corrected")
    output_path += ".lrc"


if not overwrite_lrc:
    if os.path.exists(output_path):
        log.output("The output file already exists, overwrite it? [Y/N]")
        while conf_overwrite := input():
            if conf_overwrite=='y' or conf_overwrite=='Y':
                break
            elif conf_overwrite=='n' or conf_overwrite=='N':
                log.info("User terminates program")
                log.exit()
    overwrite_lrc=True

try:
    if overwrite_lrc:
        f = open(output_path, 'w')
    else:
        log.errore("Unknown error 1")
except IOError:
    log.error("can not open lrc:"+output_path)
    log.exit()
else:
    f.close()

if not os.path.isfile(input_path):
        log.errore("can not find the input file.")
    
# try:
#     with open(input_path, 'r') as file:
#         # 尝试读取文件的前几行，确保文件是可读的
#         file.read(1)
# except (IOError, OSError):
#     log.errore("can not read the input file.")


srt_to_lrc(input_path, output_path)
log.info(f"Conversion complete. LRC file saved as '{output_path}'.")
