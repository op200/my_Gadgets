import re
import socket
import subprocess
import sys
from dataclasses import dataclass
from operator import attrgetter


@dataclass
class HostEntry:
    ip: str
    delay: float = float("inf")  # 默认延迟为无穷大（表示不可达）


def resolve_dns(hostname):
    """绕过本地hosts直接查询DNS获取所有IPv4地址"""
    try:
        # 创建一个新的DNS解析器
        resolver = socket.getaddrinfo
        # 强制使用DNS查询（某些系统可能需要其他方法）
        return set(
            item[4][0]
            for item in resolver(hostname, None, socket.AF_INET, socket.SOCK_STREAM)
            if item[0] == socket.AF_INET
        )
    except socket.gaierror:
        print(f"无法解析域名: {hostname}")
        return set()


def measure_ping(ip):
    """测量IP的延迟（毫秒），支持跨平台"""
    param = "-n" if sys.platform.lower().startswith("win") else "-c"
    count = "3"  # 发送n个ping包取平均值

    try:
        output = subprocess.check_output(
            ["ping", param, count, ip],
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            timeout=5,
        )

        # 解析输出获取延迟
        if "win" in sys.platform:
            match = re.search(r"(\d+)ms", output)
            if match:
                return float(match.group(1))
            else:
                return float("inf")  # 匹配失败，返回超时
        else:
            # Linux/macOS格式: "rtt min/avg/max/mdev = 12.345/23.456/34.567/8.910 ms"
            stats_line = output.splitlines()[-1]
            return float(stats_line.split("/")[-3])
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, IndexError):
        return float("inf")  # 标记为不可达


def remove_existing_hosts_entry(hostname):
    """从系统hosts文件中移除指定域名的记录"""
    hosts_path = (
        r"C:\Windows\System32\drivers\etc\hosts"
        if sys.platform == "win32"
        else "/etc/hosts"
    )

    try:
        with open(hosts_path, "r", encoding="utf-8-sig") as f:
            lines = f.readlines()

        modified = False
        new_lines = []
        is_前一行是空行: bool = False
        for line in lines:
            # 跳过空行
            if not line.strip():
                if is_前一行是空行 is False:
                    new_lines.append(line)
                    is_前一行是空行 = True
                continue

            is_前一行是空行 = False

            # 检查是否包含目标域名
            parts = line.split()
            if hostname not in parts:
                new_lines.append(line)
            else:
                modified = True
                print(f"已移除hosts中的记录: {line.strip()}")

        if modified:
            with open(hosts_path, "w", encoding="utf-8-sig") as f:
                f.writelines(new_lines)
            print("hosts文件已更新，旧记录已移除")
        else:
            print("hosts文件中未找到该域名的记录")

    except PermissionError:
        print("警告: 需要管理员权限修改hosts文件，请使用sudo/管理员身份运行")
        return False
    except FileNotFoundError:
        print("警告: 找不到hosts文件")
        return False
    return True


def main(hostname: str):
    entries = []

    # 0. 先移除hosts中的旧记录
    if not remove_existing_hosts_entry(hostname):
        print("继续执行，但可能无法获取最新DNS结果")

    # 1. DNS解析
    ips = resolve_dns(hostname)
    if not ips:
        print("未找到有效IP地址")
        return

    print(f"解析到 {len(ips)} 个IP地址:")

    # 2. 测试每个IP的延迟
    for ip in ips:
        print(f"正在测试 {ip}...", end=" ", flush=True)
        delay = measure_ping(ip)
        status = f"{delay:.2f}ms" if delay != float("inf") else "超时"
        print(status)
        entries.append(HostEntry(str(ip), delay))

    # 3. 按延迟排序（可用的排在前面）
    entries.sort(key=attrgetter("delay"))

    # 4. 写入hosts文件（使用追加模式）
    with open(
        (
            r"C:\Windows\System32\drivers\etc\hosts"
            if sys.platform == "win32"
            else "/etc/hosts"
        ),
        "a",  # 改为追加模式
        encoding="utf-8-sig",
    ) as f:
        f.write(f"\n# 以下是对 {hostname} 的测速结果（由脚本自动生成）\n")
        for entry in entries:
            if entry.delay != float("inf"):
                f.write(f"{entry.ip}\t{hostname}\t# {entry.delay:.2f}ms\n")


if __name__ == "__main__":
    for h in {
        "upos-sz-estgcos.bilivideo.com": 0,
        "upos-sz-estgoss.bilivideo.com": 0,
        "upos-sz-estghw.bilivideo.com": 0,
        "upos-sz-mirror08h.bilivideo.com": 0,
        # 利用静态检查去重
    }:
        main(h)
