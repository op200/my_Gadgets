import asyncio
import re
import socket
import subprocess
import sys
from dataclasses import dataclass
from operator import attrgetter

from easyrip import log

log.write_level = log.LogLevel.none
log.init()


@dataclass
class HostEntry:
    ip: str
    delay: float = float("inf")  # 默认延迟为无穷大（表示不可达）


async def resolve_dns(hostname: str):
    """异步 DNS 解析"""
    loop = asyncio.get_running_loop()
    try:
        # 使用loop.getaddrinfo的异步版本
        infos = await loop.getaddrinfo(
            hostname, None, family=socket.AF_INET, type=socket.SOCK_STREAM
        )
        return set(info[4][0] for info in infos if info[0] == socket.AF_INET)
    except socket.gaierror:
        log.error(f"无法解析域名: {hostname}")
        return set()


async def measure_ping(ip):
    """异步测量 IP 的延迟（毫秒）"""
    param = "-n" if sys.platform.lower().startswith("win") else "-c"
    count = "3"  # 发送n个ping包取平均值

    try:
        # 使用asyncio.create_subprocess_exec创建异步子进程
        proc = await asyncio.create_subprocess_exec(
            "ping", param, count, ip, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=5)
            output = stdout.decode("utf-8", errors="ignore")

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
        except asyncio.TimeoutError:
            proc.kill()
            return float("inf")
    except (subprocess.SubprocessError, IndexError):
        return float("inf")  # 标记为不可达


async def remove_existing_hosts_entry(hostname: str):
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
                log.info(f"- 已移除 hosts 中的记录: {line.strip()}")

        if modified:
            with open(hosts_path, "w", encoding="utf-8-sig") as f:
                f.writelines(new_lines)
            log.info(f"hosts 文件已更新，域名 {hostname} 的旧记录已移除")
        else:
            log.info(f"hosts 文件中未找到域名 {hostname} 的记录")

    except PermissionError:
        log.error("需要管理员权限修改 hosts 文件")
        return False
    except FileNotFoundError:
        log.error("找不到 hosts 文件")
        return False
    return True


async def async_main(hostname: str):
    """异步版本的main函数"""
    entries = list[HostEntry]()

    # 0. 先移除 hosts 中的旧记录
    if not await remove_existing_hosts_entry(hostname):
        log.warning("移除 hosts 中的旧记录函数执行失败，终止程序")
        return

    # 1. DNS解析
    ips = await resolve_dns(hostname)
    if not ips:
        log.error("未找到有效 IP 地址，终止程序")
        return

    log.info(f"! 解析到 {hostname:<36} 有 {len(ips):<2} 个 IP")

    # 2. 并发测试每个IP的延迟
    tasks = [measure_ping(ip) for ip in ips]
    delays = await asyncio.gather(*tasks)

    for ip, delay in zip(ips, delays):
        log.info(
            f"? 测试　 {hostname:<36} {ip:<20} {f'{delay:<6.2f} ms' if delay != float('inf') else '超时'}"
        )
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
        for entry in entries[:5]:  # 只取前五个写入
            if entry.delay != float("inf"):
                s = f"{entry.ip}\t{hostname}\t# {entry.delay:.2f}ms"
                f.write(f"{s}\n")
                log.info(f"+ 已写入 {s}")


async def run_all_hosts():
    """并发执行所有域名的测试"""
    hosts = {
        "www.bilibili.com": 0,
        "api.bilibili.com": 0,
        "b23.tv": 0,
        "data.bilibili.com": 0,
        "i0.hdslb.com": 0,
        "i1.hdslb.com": 0,
        "s1.hdslb.com": 0,
        "upos-sz-302kodo.bilivideo.com": 0,
        "upos-sz-estgcos.bilivideo.com": 0,
        "upos-sz-estgoss.bilivideo.com": 0,
        "upos-sz-estghw.bilivideo.com": 0,
        "upos-sz-mirror08h.bilivideo.com": 0,
        "upos-sz-mirror08c.bilivideo.com": 0,
        "upos-sz-mirrorcos.bilivideo.com": 0,
    }

    # 并发执行所有域名的测试
    tasks = [async_main(host) for host in hosts]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(run_all_hosts())
