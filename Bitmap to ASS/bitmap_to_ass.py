import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Final

import cv2
import numpy as np
import pyperclip
from easyrip import log
from tqdm import tqdm

log.write_level = log.LogLevel.none

PROJECT_NAME = "Bitmap to ASS"
PROJECT_LINK = "https://github.com/op200/my_Gadgets"
__version__ = "1.0.0"


argparser = argparse.ArgumentParser()
argparser.add_argument("-v", "--version", action="store_true", help="print version")
argparser.add_argument("--debug", action="store_true", help="debug log")
argparser.add_argument("-i", "--input", help="input image")
argparser.add_argument(
    "-c", "--copy", action="store_true", help="copy the output to clipboard"
)
argparser.add_argument(
    "-p", "--print", action="store_true", help="print the output to terminal"
)
argparser.add_argument(
    "-t",
    "--threshold",
    type=float,
    help="color threshold",
    default=0,
)


def rgba_to_tag(
    r: np.uint8,
    g: np.uint8,
    b: np.uint8,
    a: np.uint8,
    default_bgr: np.uint32,
    default_alpha: np.uint8,
) -> str:
    bgr: np.uint32 = b * np.uint32(65536) + g * np.uint32(256) + r
    c_str = "" if bgr == default_bgr else f"{bgr:X}"
    return rf"\c{c_str}{('' if a == default_alpha else rf'\1a{a:X}')}"


def get_th(
    rgba_tuple_1: tuple[np.uint8, np.uint8, np.uint8, np.uint8],
    rgba_tuple_2: tuple[np.uint8, np.uint8, np.uint8, np.uint8],
):
    return abs(sum(map(np.uint16, rgba_tuple_1)) - sum(map(np.uint16, rgba_tuple_2)))


if __name__ == "__main__":
    args = argparser.parse_args()

    if args.debug:
        log.print_level = log.LogLevel.debug

    log.debug(args)

    if args.version:
        log.send(
            f"{PROJECT_NAME} version {__version__}\n{PROJECT_LINK}", is_format=False
        )
        sys.exit(0)

    if not args.input:
        log.error("Need --input")
        sys.exit(1)

    img_path = Path(args.input)
    img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)

    if img is None:
        log.error("Decode img failed")
        sys.exit(2)

    # 转换为RGBA格式
    if img.shape[2] == 3:  # 如果是RGB/BGR格式
        img_rgba = cv2.cvtColor(img, cv2.COLOR_BGR2RGBA)
    elif img.shape[2] == 4:  # 如果已经是RGBA格式
        img_rgba = cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA)  # BGRA转RGBA
    else:
        # 对于灰度图或其他格式，转换为RGBA
        if len(img.shape) == 2:  # 灰度图
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        img_rgba = cv2.cvtColor(img, cv2.COLOR_BGR2RGBA)

    # 获取图像尺寸
    height: int
    width: int
    channels: int
    height, width, channels = img_rgba.shape
    log.debug("img size: {}x{}, channels: {}", width, height, channels)

    # 使用reshape一次性获取所有像素数据
    # 将图像展平为(N, 4)的数组，N=像素总数
    pixels_flat: np.typing.NDArray[np.uint8] = img_rgba.reshape(-1, 4)  # pyright: ignore[reportAssignmentType]
    log.debug(
        "flat type: {}: {} {} {} {}",
        type(pixels_flat.dtype),
        type(pixels_flat[:, 0].dtype),
        type(pixels_flat[:, 1].dtype),
        type(pixels_flat[:, 2].dtype),
        type(pixels_flat[:, 3].dtype),
    )
    log.debug("pix count: {:,}", len(pixels_flat))

    rgb_uint32 = (
        (pixels_flat[:, 2].astype(np.uint32) << 16)
        | (pixels_flat[:, 1].astype(np.uint32) << 8)
        | pixels_flat[:, 0].astype(np.uint32)
    )
    default_bgr: np.uint32
    default_bgr, _default_rgb_count = Counter(rgb_uint32).most_common(1)[0]
    log.info("Default BGR: {rgb} &H{rgb:X}&", rgb=default_bgr)
    log.debug(
        "Default BGR count: {:,} {:.2%}",
        _default_rgb_count,
        _default_rgb_count / len(pixels_flat),
    )

    default_alpha: np.uint8
    default_alpha, _default_alpha_count = Counter(pixels_flat[:, 3]).most_common(1)[0]
    log.info("Default Alpha: {a} &H{a:X}&", a=default_alpha)
    log.debug(
        "Default Alpha count: {:,} {:.2%}",
        _default_alpha_count,
        _default_alpha_count / len(pixels_flat),
    )

    output_ass_draw_list: Final[list[str]] = [r"{\an7\pos(0,0)\p1}m"]

    # 遍历所有像素
    pre_x: int = 0
    pre_y: int = -1
    pre_rgba_tuple: tuple[np.uint8, np.uint8, np.uint8, np.uint8] | None = None
    for i, rgba in tqdm(
        enumerate(pixels_flat),
        total=len(pixels_flat),
        unit="px",
    ):
        # 计算原始坐标
        x = i % width
        y = i // width

        rgba_tuple: tuple[np.uint8, np.uint8, np.uint8, np.uint8] = tuple(rgba)

        # 换行闭合
        if y != pre_y:
            w = width - pre_x
            output_ass_draw_list.append(
                rf"l{w} 0 {w} 1 0 1"
                r"{\p0}\N"
                rf"{{\p1{rgba_to_tag(*rgba_tuple, default_bgr, default_alpha) if rgba_tuple != pre_rgba_tuple else ''}}}m0 0"
            )
            pre_x = 0
            pre_y = y
            pre_rgba_tuple = rgba_tuple

        # 换色闭合
        if rgba_tuple != pre_rgba_tuple and (
            pre_rgba_tuple is None
            or args.threshold == 0
            or get_th(rgba_tuple, pre_rgba_tuple) > args.threshold
        ):
            w = x - pre_x
            output_ass_draw_list.append(
                rf"l{w} 0 {w} 1 0 1{{{rgba_to_tag(*rgba_tuple, default_bgr, default_alpha)}}}m0 0"
            )
            pre_x = x
            pre_rgba_tuple = rgba_tuple

    output_str: str = "".join(output_ass_draw_list)

    log.info("Output length: {:,} B", len(output_str))
    log.info("String size: {:,.3f} MiB", len(output_str) / (1024**2))

    if args.print:
        print(output_str)

    if args.copy:
        try:
            pyperclip.copy(output_str)
        except Exception as e:
            log.debug("{!r}", e)
            log.error("Copy to clipboard failed: {}", e)
