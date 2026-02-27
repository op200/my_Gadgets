import argparse
import re
from pathlib import Path

from easyrip import log
from easyrip.utils import read_text

log.write_level = log.LogLevel.none

__version__ = "0.1.0"


def convert_timecode_format(text):
    """
    将时间码格式中的小数点改为逗号
    格式: 00:00:00.000 --> 00:00:00.000
    """
    # 严格匹配时间码格式的正则表达式
    pattern = r"(\d{2}:\d{2}:\d{2})\.(\d{3})\s+-->\s+(\d{2}:\d{2}:\d{2})\.(\d{3})"

    def replace_dot(match):
        # 将匹配到的时间码中的小数点替换为逗号
        return (
            f"{match.group(1)},{match.group(2)} --> {match.group(3)},{match.group(4)}"
        )

    # 使用re.sub进行替换，只替换完全匹配格式的字符串
    result = re.sub(pattern, replace_dot, text)

    return result


def vtt_to_srt(
    input_path: Path,
    output_path: Path,
    /,
    *,
    encoding: str | None = None,
):
    line_list: list[str] = []
    for line in (
        read_text(input_path)
        if encoding is None
        else input_path.read_text(encoding=encoding)
    ).splitlines():
        line_list.append(convert_timecode_format(line))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.touch()

    output_path.write_text("\n".join(line_list), encoding="utf-8")


def main():
    """命令行入口函数"""
    parser = argparse.ArgumentParser(
        description="将VTT字幕文件转换为SRT格式（将时间码中的小数点改为逗号）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s -i input.vtt -o output.srt
  %(prog)s --input input.vtt --output output.srt
  %(prog)s -i input.vtt -o output.srt --encoding utf-8
        """,
    )

    parser.add_argument(
        "-v", "--version", action="version", version=f"%(prog)s {__version__}"
    )

    parser.add_argument(
        "-i", "--input", type=Path, required=True, help="输入的 VTT 文件路径"
    )

    parser.add_argument(
        "-o", "--output", type=Path, required=True, help="输出的 SRT 文件路径"
    )

    parser.add_argument(
        "-e",
        "--encoding",
        type=str,
        default=None,
        help="输入文件解码格式，Python 的 encoding 形参 (默认支持所有带 BOM 的 UTF)",
    )

    args = parser.parse_args()

    try:
        # 检查输入文件是否存在
        if not args.input.exists():
            log.error(f"输入文件不存在 - {args.input}")
            return 1

        # 执行转换
        vtt_to_srt(args.input, args.output, encoding=args.encoding)
        log.info(f"成功将 {args.input} 转换为 {args.output}")
        return 0

    except Exception as e:
        log.error(f"转换过程中发生异常 - {e}")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
