import ctypes
import datetime
import os
import sys
from pathlib import Path
from typing import Callable

import numpy as np
from scenedetect import SceneManager, StatsManager, open_video
from scenedetect.detectors import ContentDetector
from scenedetect.video_stream import VideoOpenFailure

PROGRAM_NAME = "检测转场生成关键帧文件"
VERSION = "0.3.0"
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


def change_title(title: str) -> None:
    if os.name == "nt":
        ctypes.windll.kernel32.SetConsoleTitleW(title)
    elif os.name == "posix":
        sys.stdout.write(f"\x1b]2;{title}\x07")
        sys.stdout.flush()


class TXT:
    line_num = 0

    def __init__(self, path: Path, overwrite_txt: bool):
        f = None
        try:
            assert overwrite_txt is True, "Unknown error 1: overwrite_txt is False"
            f = path.open("w")
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
            self.srt = self.path.open("a", newline="\n")
        except IOError:
            log.error(f'Can not open the txt "{self.path}"')
            raise
        self.write_line("# keyframe format v1\nfps 0\n0")

    def write_line(self, line: object):
        self.srt.write(f"{line}\n")

    def end_write(self):
        self.srt.close()


# 开始
def find_scenes(
    video_path: Path,
    *,
    threshold: float,
    min_scene_len: int,
    show_progress: bool,
    callback: Callable[[np.ndarray, int], None] | None = None,
):
    # 打开视频
    try:
        video = open_video(str(video_path.resolve()))
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

    # 开始场景检测
    scene_manager.detect_scenes(
        frame_source=video,
        show_progress=show_progress,
        callback=callback,
    )

    # 获取场景列表
    return scene_manager.get_scene_list()


if __name__ == "__main__":
    cmds = sys.argv[1:]

    input_path: Path | str | None = None
    output_path: Path | str | None = None
    overwrite_txt: bool = False

    threshold: int = 27
    min_scene_len: int = 1

    is_print_frame_num: bool = False

    for cmd in cmds:
        match cmd:
            case "-v" | "-ver" | "-version":
                print(f"{PROGRAM_NAME}\nVersion: {VERSION}\n{HOME_LINK}")
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
    default: 0""")
                sys.exit(0)

    for i in range(len(cmds)):
        match cmds[i]:
            case "-i" | "-input":
                input_path = cmds[i + 1]

            case "-o" | "-output":
                output_path = cmds[i + 1]

            case "-th" | "-threshold":
                try:
                    threshold = int(cmds[i + 1])
                except Exception as e:
                    log.error(f"threshold value error: {e}")
                    sys.exit(1)

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

    input_path = Path(input_path)
    output_path = Path(output_path)

    if output_path.suffix != ".txt":
        log.warning(
            "The suffix of the output file is not '.txt' and has been automatically corrected"
        )
        output_path = output_path.with_name(f"{output_path.name}.txt")

    if overwrite_txt is False:
        if output_path.is_file():
            log.output("The output file already exists, overwrite it? [Y/N]")
            while conf_overwrite := input():
                match conf_overwrite.lower():
                    case "y":
                        break
                    case "n":
                        log.info("User exit program")
                        sys.exit(0)
        overwrite_txt = True

    log.info("Start detection")

    try:
        txt = TXT(output_path, overwrite_txt)
        txt.start_write()
    except IOError as e:
        log.error(e)
        sys.exit(1)

    try:
        find_scenes(
            input_path,
            threshold=threshold,
            min_scene_len=min_scene_len,
            show_progress=(not is_print_frame_num),
            callback=(
                (lambda frame_img, frame_num: print(frame_num))
                if is_print_frame_num
                else (lambda frame_img, frame_num: txt.write_line(frame_num))
            ),
        )
    except KeyboardInterrupt:
        log.info("User exit program")
    finally:
        txt.end_write()

    log.info("END")
    change_title("END")
