import cv2
# import numpy as np

from scenedetect import open_video, SceneManager, StatsManager
from scenedetect.detectors import ContentDetector

import sys
import os
# os.environ['KMP_DUPLICATE_LIB_OK']='True'

PROGRAM_NAME = "检测转场生成关键帧文件"
VERSION = "0.1.1"
HOME_LINK = "https://github.com/op200/my_Gadgets"


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




cmds = sys.argv[1:]

input_path:str = None
output_path:str = None
overwrite_txt:bool = False

threshold:int = 27
min_scene_len:int = 1

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
    default: {overwrite_txt}

-th/-threshold <int>
    Set threshold for transition detection
    default: {threshold}

-ml/-minlen <int>
    Set min_scene_len for transition detection
    default: {min_scene_len}

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

    # overwrite txt
    if cmds[i]=="-ow":
        overwrite_txt = True

    # threshold
    if cmds[i]=="-th" or cmds[i]=="-threshold":
        try:
            threshold = int(cmds[i+1])
        except:
            log.errore("threshold value error")

    # threshold
    if cmds[i]=="-ml" or cmds[i]=="-minlen":
        try:
            min_scene_len = int(cmds[i+1])
        except:
            log.errore("min_scene_len value error")
    
    # log level
    if cmds[i]=="-loglevel":
        try:
            log.log_level = int(cmds[i+1])
        except:
            log.errore("log level error")



if not input_path:
    log.errore("Missing input file")
if not output_path:
    log.errore("Missing output file")

if output_path[-4:] != ".txt":
    log.warning("The suffix of the output file is not '.txt' and has been automatically corrected")
    output_path += ".txt"

if not overwrite_txt and os.path.exists(output_path):
    log.warning("The output file already exists, overwrite it? [Y/N]",80)
    while conf_overwrite := input():
        if conf_overwrite=='y' or conf_overwrite=='Y':
            overwrite_txt=True
            break
        elif conf_overwrite=='n' or conf_overwrite=='N':
            log.info("User terminates program")
            log.exit()



# 载入视频
video_cap = cv2.VideoCapture(input_path)
if not video_cap.isOpened():
    log.errore("video can't be readed")
    pass
log.info("open video complete", 10)
video_cap.release()

class TXT:
    line_num = 0

    def __init__(self, path:str):
        try:
            if overwrite_txt:
                f = open(path, 'w')
            else:
                log.errore("Unknown error 1")
        except IOError:
            log.error("can not open txt:"+path)
            log.exit()
        else:
            f.close()
            self.path = path
            self.line_num = 1
    
    def start_write(self):
        try:
            self.srt = open(self.path, 'a')
        except IOError:
            log.error("can not open txt:"+self.path)
            log.exit()
        self.writeLine("# keyframe format v1\nfps 0")

    def writeLine(self, line:object):
        self.srt.write(f"{line}\n")

    def end_write(self):
        self.srt.close()


# 开始
def find_scenes(video_path):
    # 打开视频
    video = open_video(video_path)

    # 创建统计管理器对象
    stats_manager = StatsManager()

    # 创建场景管理器对象，并添加内容检测器
    scene_manager = SceneManager(stats_manager)
    scene_manager.add_detector(
        ContentDetector(threshold=threshold, min_scene_len=min_scene_len)
    )

    # 开始场景检测
    scene_manager.detect_scenes(frame_source=video)

    # 获取场景列表
    return scene_manager.get_scene_list()


log.info("Start detection")

txt = TXT(output_path)
txt.start_write()
for frame_info in find_scenes(input_path):
    txt.writeLine(frame_info[0].frame_num)


log.info("END")