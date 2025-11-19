import datetime
import os
import sys

from scenedetect import SceneManager, StatsManager, open_video
from scenedetect.detectors import ContentDetector
from scenedetect.video_stream import VideoOpenFailure

PROGRAM_NAME = "检测转场生成关键帧文件"
VERSION = "0.2.2"
HOME_LINK = "https://github.com/op200/my_Gadgets"


# 日志
class log:
    log_level = 0

    @classmethod
    def output(cls, msg: object):
        print(
            f"\033[32m{datetime.datetime.now().strftime('%Y.%m.%d %H:%M:%S.%f')[:-4]}\033[35m {msg}\033[0m"
        )

    @classmethod
    def error(cls, msg: object, level: int = 110):
        if level > cls.log_level:
            cls.output(f"\033[31m[ERROR] {msg}")

    @classmethod
    def warning(cls, msg: object, level: int = 70):
        if level > cls.log_level:
            cls.output(f"\033[33m[WARNING] {msg}")

    @classmethod
    def info(cls, msg: object, level: int = 30):
        if level > cls.log_level:
            cls.output(f"\033[34m[INFO] {msg}")


def change_title(title: str):
    if os.name == "nt":
        os.system(f"title {title}")
    elif os.name == "posix":
        sys.stdout.write(f"\x1b]2;{title}\x07")
        sys.stdout.flush()


cmds = sys.argv[1:]

input_path: str | None = None
output_path: str | None = None
overwrite_txt: bool = False

threshold: int = 27
min_scene_len: int = 1

is_print_frame_num: bool = False

for cmd in cmds:
    match cmd:
        case "-v" | "-ver" | "-version":
            log.output(f"{PROGRAM_NAME}\nVersion: {VERSION}\n{HOME_LINK}")
            sys.exit(0)
        case "-h" | "-help":
            print(f"""
    {PROGRAM_NAME} v{VERSION} help:

    -h / -help
        print help

    -v / -ver / -version
        print version

    -i / -input <string>
        the input path of a video or img sequence
        Default: {input_path}

    -o / -output <string>
        the output path of txt
        Default: {output_path}

    -th / -threshold <int>
        Set threshold for transition detection
        Default: {threshold}

    -ml / -minlen <int>
        Set min_scene_len for transition detection
        Default: {min_scene_len}

    -ow
        is it overwrite txt
        Default: {overwrite_txt}

    -print
        Print the detected frame num
        Default: {is_print_frame_num}

    -loglevel <int>
        Log level
        if it > 20 , some INFO    will not be print
        if it > 40 , all  INFO    will not be print
        if it > 60 , some WARRING will not be print
        if it > 80 , all  WARRING will not be print
        if it > 100, some ERROR   will not be print
        if it > 120, all  ERROR   will not be print
        if it > 140, all  logs    will not be print
        default: 0
            """)
            sys.exit(0)

for i in range(len(cmds)):
    match cmds[i]:
        # input
        case "-i" | "-input":
            input_path = cmds[i + 1]

        # output
        case "-o" | "-output":
            output_path = cmds[i + 1]

        # threshold
        case "-th" | "-threshold":
            try:
                threshold = int(cmds[i + 1])
            except Exception as e:
                log.error(f"threshold value error: {e}")
                sys.exit(1)

        # threshold
        case "-ml" | "-minlen":
            try:
                min_scene_len = int(cmds[i + 1])
            except Exception as e:
                log.error(f"min_scene_len value error: {e}")
                sys.exit(1)

        # overwrite txt
        case "-ow":
            overwrite_txt = True

        # print frame num
        case "-print":
            is_print_frame_num = True

        # log level
        case "-loglevel":
            try:
                log.log_level = int(cmds[i + 1])
            except Exception as e:
                log.error(f"log level error: {e}")
                sys.exit(1)


if not input_path:
    log.error("Missing input file")
    sys.exit(1)

if not output_path:
    log.error("Missing output file")
    sys.exit(1)

elif output_path[-4:] != ".txt":
    log.warning(
        "The suffix of the output file is not '.txt' and has been automatically corrected"
    )
    output_path += ".txt"


if overwrite_txt is False:
    if os.path.exists(output_path):
        log.output("The output file already exists, overwrite it? [Y/N]")
        while conf_overwrite := input():
            match conf_overwrite.lower():
                case "y":
                    break
                case "n":
                    log.info("User exit program")
                    sys.exit(0)
    overwrite_txt = True


class TXT:
    line_num = 0

    def __init__(self, path: str):
        f = None
        try:
            assert overwrite_txt is True, "Unknown error 1: overwrite_txt is False"
            f = open(path, "w")
        except IOError:
            log.error(f"can not open txt: {path}")
            raise
        finally:
            if f:
                f.close()

        self.path = path
        self.line_num = 1

    def start_write(self):
        try:
            self.srt = open(self.path, "a")
        except IOError:
            log.error("can not open txt:" + self.path)
            raise
        self.write_line("# keyframe format v1\nfps 0")

    def write_line(self, line: object):
        self.srt.write(f"{line}\n")

    def end_write(self):
        self.srt.close()


# 开始
def find_scenes(video_path):
    # 打开视频
    try:
        video = open_video(video_path)
    except VideoOpenFailure as e:
        log.error(f"Open video error: {e}")
        sys.exit(1)

    # 创建统计管理器对象
    stats_manager = StatsManager()

    # 创建场景管理器对象，并添加内容检测器
    scene_manager = SceneManager(stats_manager)
    scene_manager.add_detector(
        ContentDetector(threshold=threshold, min_scene_len=min_scene_len)
    )

    show_progress: bool = True
    if is_print_frame_num:
        show_progress: bool = False

        def _scene_manager_callback(frame_img, frame_num: int):
            print(frame_num)
    else:

        def _scene_manager_callback(frame_img, frame_num: int):
            pass

    # 开始场景检测
    scene_manager.detect_scenes(
        frame_source=video,
        show_progress=show_progress,
        callback=_scene_manager_callback,
    )

    # 获取场景列表
    return scene_manager.get_scene_list()


if __name__ == "__main__":
    log.info("Start detection")

    try:
        txt = TXT(output_path)
        txt.start_write()
    except IOError:
        sys.exit(1)

    try:
        for frame_info in find_scenes(input_path):
            txt.write_line(frame_info[0].frame_num)
    except KeyboardInterrupt:
        log.info("User exit program")
    finally:
        txt.end_write()

    log.info("END")
    change_title("END")
