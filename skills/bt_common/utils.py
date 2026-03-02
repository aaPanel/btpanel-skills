# /// script
# dependencies = []
# ///
"""
工具函数模块
提供格式化输出、阈值检查、告警生成等功能
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class Alert:
    """告警信息"""

    level: str  # warning, critical
    type: str  # cpu, memory, disk, service, ssl, security
    message: str
    value: Optional[float] = None
    extra: dict = field(default_factory=dict)


def format_bytes(bytes_value: int, decimals: int = 2) -> str:
    """
    格式化字节大小为人类可读格式

    Args:
        bytes_value: 字节数
        decimals: 小数位数

    Returns:
        格式化后的字符串
    """
    if bytes_value == 0:
        return "0 B"

    k = 1024
    sizes = ["B", "KB", "MB", "GB", "TB", "PB"]
    i = 0
    value = float(bytes_value)

    while value >= k and i < len(sizes) - 1:
        value /= k
        i += 1

    return f"{value:.{decimals}f} {sizes[i]}"


def format_uptime(seconds: int) -> str:
    """
    格式化运行时间

    Args:
        seconds: 秒数

    Returns:
        格式化后的字符串
    """
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60

    if days > 0:
        return f"{days}天{hours}小时"
    if hours > 0:
        return f"{hours}小时{minutes}分钟"
    return f"{minutes}分钟"


def format_timestamp(ts: Optional[str] = None) -> str:
    """
    格式化时间戳

    Args:
        ts: ISO格式时间戳，为None时使用当前时间

    Returns:
        格式化后的时间字符串
    """
    if ts:
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, AttributeError):
            return ts
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def parse_system_monitor_data(data: dict, server_name: str) -> dict:
    """
    解析系统监控数据（GetNetWork接口返回）

    Args:
        data: 原始API响应
        server_name: 服务器名称

    Returns:
        格式化后的系统监控数据
    """
    result = {
        "server": server_name,
        "timestamp": datetime.now().isoformat(),
        "version": data.get("version", "unknown"),
        "hostname": data.get("title", "unknown"),
        "system": data.get("simple_system", data.get("system", "unknown")),
        "uptime": data.get("time", "unknown"),
        "docker_running": data.get("docker_run", False),
    }

    # 解析CPU数据
    # cpu格式: [使用率%, 核心数, [用户态%, 系统态%], CPU型号, ?, ?]
    cpu_data = data.get("cpu", [])
    if isinstance(cpu_data, list) and len(cpu_data) >= 4:
        result["cpu"] = {
            "usage": round(cpu_data[0], 2) if isinstance(cpu_data[0], (int, float)) else 0,
            "cores": cpu_data[1] if isinstance(cpu_data[1], int) else 1,
            "user_usage": round(cpu_data[2][0], 2) if isinstance(cpu_data[2], list) and len(cpu_data[2]) > 0 else 0,
            "system_usage": round(cpu_data[2][1], 2) if isinstance(cpu_data[2], list) and len(cpu_data[2]) > 1 else 0,
            "model": cpu_data[3] if isinstance(cpu_data[3], str) else "Unknown",
        }
    else:
        result["cpu"] = {"usage": 0, "cores": 1, "model": "Unknown"}

    # 解析CPU时间分布
    cpu_times = data.get("cpu_times", {})
    if cpu_times:
        result["cpu"]["times"] = {
            "user": round(cpu_times.get("user", 0), 2),
            "system": round(cpu_times.get("system", 0), 2),
            "idle": round(cpu_times.get("idle", 0), 2),
            "iowait": round(cpu_times.get("iowait", 0), 2),
        }
        # 进程数
        result["processes"] = {
            "total": cpu_times.get("总进程数", 0),
            "active": cpu_times.get("活动进程数", 0),
        }

    # 解析负载
    load_data = data.get("load", {})
    if load_data:
        result["load"] = {
            "one_minute": round(load_data.get("one", 0), 2),
            "five_minute": round(load_data.get("five", 0), 2),
            "fifteen_minute": round(load_data.get("fifteen", 0), 2),
            "cpu_count": load_data.get("max", 1),
            "safe_limit": load_data.get("safe", 1),
        }

    # 解析内存数据 (单位: MB)
    mem_data = data.get("mem", {})
    if mem_data:
        mem_total = mem_data.get("memTotal", 0)
        mem_free = mem_data.get("memFree", 0)
        mem_cached = mem_data.get("memCached", 0)
        mem_buffers = mem_data.get("memBuffers", 0)
        mem_available = mem_data.get("memAvailable", 0)
        mem_used = mem_data.get("memRealUsed", mem_total - mem_free)

        result["memory"] = {
            "total_mb": mem_total,
            "total_gb": round(mem_total / 1024, 2),
            "used_mb": mem_used,
            "used_gb": round(mem_used / 1024, 2),
            "free_mb": mem_free,
            "available_mb": mem_available,
            "cached_mb": mem_cached,
            "buffers_mb": mem_buffers,
            "percent": round((mem_used / mem_total * 100), 2) if mem_total > 0 else 0,
            "available_percent": round((mem_available / mem_total * 100), 2) if mem_total > 0 else 0,
        }

    # 解析磁盘数据
    disk_list = data.get("disk", [])
    disks = []
    total_size = 0
    total_used = 0

    for disk in disk_list:
        if isinstance(disk, dict):
            byte_size = disk.get("byte_size", [0, 0, 0])
            size_info = disk.get("size", ["0", "0", "0", "0%"])

            disk_total = byte_size[0] if isinstance(byte_size, list) and len(byte_size) > 0 else 0
            disk_used = byte_size[1] if isinstance(byte_size, list) and len(byte_size) > 1 else 0
            disk_free = byte_size[2] if isinstance(byte_size, list) and len(byte_size) > 2 else 0

            # 跳过挂载的远程存储（如ossfs）
            filesystem = disk.get("filesystem", "")
            if "fuse" in filesystem.lower() or "ossfs" in filesystem.lower():
                continue

            disk_entry = {
                "path": disk.get("path", "/"),
                "filesystem": filesystem,
                "type": disk.get("type", "unknown"),
                "total_bytes": disk_total,
                "used_bytes": disk_used,
                "free_bytes": disk_free,
                "total_human": size_info[0] if len(size_info) > 0 else "0",
                "used_human": size_info[1] if len(size_info) > 1 else "0",
                "free_human": size_info[2] if len(size_info) > 2 else "0",
                "percent": float(size_info[3].replace("%", "").strip()) if len(size_info) > 3 and isinstance(size_info[3], str) else 0,
                "name": disk.get("rname", disk.get("path", "/")),
            }
            disks.append(disk_entry)
            total_size += disk_total
            total_used += disk_used

    result["disk"] = {
        "disks": disks,
        "total_bytes": total_size,
        "used_bytes": total_used,
        "free_bytes": total_size - total_used,
        "total_human": format_bytes(total_size),
        "used_human": format_bytes(total_used),
        "free_human": format_bytes(total_size - total_used),
        "percent": round((total_used / total_size * 100), 2) if total_size > 0 else 0,
    }

    # 解析网络数据
    result["network"] = {
        "total_up": format_bytes(data.get("upTotal", 0)),
        "total_down": format_bytes(data.get("downTotal", 0)),
        "current_up": round(data.get("up", 0), 2),  # KB/s
        "current_down": round(data.get("down", 0), 2),  # KB/s
        "up_packets": data.get("upPackets", 0),
        "down_packets": data.get("downPackets", 0),
        "interfaces": {},
    }

    # 各网卡数据
    network_ifaces = data.get("network", {})
    for iface, stats in network_ifaces.items():
        if isinstance(stats, dict):
            result["network"]["interfaces"][iface] = {
                "up_total": format_bytes(stats.get("upTotal", 0)),
                "down_total": format_bytes(stats.get("downTotal", 0)),
                "current_up": round(stats.get("up", 0), 2),
                "current_down": round(stats.get("down", 0), 2),
            }

    # 资源统计
    result["resources"] = {
        "sites": data.get("site_total", 0),
        "databases": data.get("database_total", 0),
        "ftp_accounts": data.get("ftp_total", 0),
    }

    # IO统计
    iostat = data.get("iostat", {})
    if iostat and "ALL" in iostat:
        all_io = iostat["ALL"]
        result["io"] = {
            "read_count": all_io.get("read_count", 0),
            "write_count": all_io.get("write_count", 0),
            "read_bytes": format_bytes(all_io.get("read_bytes", 0)),
            "write_bytes": format_bytes(all_io.get("write_bytes", 0)),
        }

    return result


def parse_system_status_legacy(data: dict, server_name: str) -> dict:
    """
    解析旧版系统状态响应（GetSystemTotal接口）

    Args:
        data: 原始API响应
        server_name: 服务器名称

    Returns:
        格式化后的系统状态
    """
    mem_total = data.get("mem_total", 0)
    mem_used = data.get("mem_used", 0)
    disk_total = data.get("disk_total", 0)
    disk_used = data.get("disk_used", 0)

    # 转换为GB
    mem_total_gb = mem_total / 1024 / 1024 / 1024 if mem_total else 0
    mem_used_gb = mem_used / 1024 / 1024 / 1024 if mem_used else 0
    disk_total_gb = disk_total / 1024 / 1024 / 1024 if disk_total else 0
    disk_used_gb = disk_used / 1024 / 1024 / 1024 if disk_used else 0

    # 计算百分比
    mem_percent = (mem_used / mem_total * 100) if mem_total > 0 else 0
    disk_percent = (disk_used / disk_total * 100) if disk_total > 0 else 0

    return {
        "server": server_name,
        "timestamp": datetime.now().isoformat(),
        "metrics": {
            "cpu": {
                "usage": float(data.get("cpu_usage", 0) or 0),
                "cores": int(data.get("cpu_core", 1) or 1),
                "model": data.get("cpu_model", "Unknown") or "Unknown",
            },
            "memory": {
                "used": round(mem_used_gb, 2),
                "total": round(mem_total_gb, 2),
                "percent": round(mem_percent, 2),
            },
            "disk": {
                "used": round(disk_used_gb, 2),
                "total": round(disk_total_gb, 2),
                "percent": round(disk_percent, 2),
            },
            "system": {
                "hostname": data.get("host_name", "Unknown") or "Unknown",
                "os": data.get("system", "Unknown") or "Unknown",
                "uptime": format_uptime(int(data.get("up_time", 0) or 0)),
            },
        },
    }


def check_thresholds(metrics: dict, thresholds: dict) -> list[Alert]:
    """
    检查阈值告警

    Args:
        metrics: 格式化后的指标数据（来自parse_system_monitor_data）
        thresholds: 阈值配置

    Returns:
        告警列表
    """
    alerts = []

    cpu_threshold = thresholds.get("cpu", 80)
    memory_threshold = thresholds.get("memory", 85)
    disk_threshold = thresholds.get("disk", 90)

    # CPU告警
    cpu_data = metrics.get("cpu", {})
    cpu_usage = cpu_data.get("usage", 0)
    if cpu_usage >= cpu_threshold:
        alerts.append(
            Alert(
                level="warning",
                type="cpu",
                message=f"CPU使用率过高: {cpu_usage}% (阈值: {cpu_threshold}%)",
                value=cpu_usage,
            )
        )

    # 内存告警
    mem_data = metrics.get("memory", {})
    mem_percent = mem_data.get("percent", 0)
    if mem_percent >= memory_threshold:
        alerts.append(
            Alert(
                level="warning",
                type="memory",
                message=f"内存使用率过高: {mem_percent}% (阈值: {memory_threshold}%)",
                value=mem_percent,
                extra={
                    "used_mb": mem_data.get("used_mb"),
                    "total_mb": mem_data.get("total_mb"),
                },
            )
        )

    # 磁盘告警
    disk_data = metrics.get("disk", {})
    disk_percent = disk_data.get("percent", 0)
    if disk_percent >= disk_threshold:
        alerts.append(
            Alert(
                level="critical",
                type="disk",
                message=f"磁盘使用率过高: {disk_percent}% (阈值: {disk_threshold}%)",
                value=disk_percent,
                extra={
                    "used_human": disk_data.get("used_human"),
                    "total_human": disk_data.get("total_human"),
                },
            )
        )

    # 检查各磁盘分区
    for disk in disk_data.get("disks", []):
        disk_p = disk.get("percent", 0)
        if disk_p >= disk_threshold:
            alerts.append(
                Alert(
                    level="critical" if disk_p >= 95 else "warning",
                    type="disk",
                    message=f"磁盘分区 {disk.get('path', '/')} 使用率过高: {disk_p}%",
                    value=disk_p,
                    extra={"path": disk.get("path")},
                )
            )

    # 负载告警
    load_data = metrics.get("load", {})
    if load_data:
        one_min_load = load_data.get("one_minute", 0)
        cpu_count = load_data.get("cpu_count", 1)
        # 负载超过CPU核心数时告警
        if one_min_load >= cpu_count:
            alerts.append(
                Alert(
                    level="warning",
                    type="load",
                    message=f"系统负载过高: {one_min_load} (CPU核心数: {cpu_count})",
                    value=one_min_load,
                )
            )

    return alerts


def format_security_report(data: dict, server_name: str) -> dict:
    """
    格式化安全报告

    Args:
        data: 原始安全数据
        server_name: 服务器名称

    Returns:
        格式化后的安全报告
    """
    return {
        "server": server_name,
        "timestamp": datetime.now().isoformat(),
        "security": {
            "firewall": {
                "status": data.get("firewall_status", "unknown"),
                "rules": data.get("firewall_rules", 0),
            },
            "ssh": {
                "failedAttempts": data.get("ssh_failed", 0),
                "lastLogin": data.get("last_login"),
                "lastLoginIp": data.get("last_login_ip"),
            },
            "suspiciousIps": data.get("suspicious_ips", []),
            "recentAlerts": data.get("security_alerts", []),
        },
    }


def format_service_status(services: list, server_name: str) -> dict:
    """
    格式化服务状态

    Args:
        services: 服务列表
        server_name: 服务器名称

    Returns:
        格式化后的服务状态
    """
    formatted_services = []
    running_count = 0
    stopped_count = 0

    for svc in services:
        status = svc.get("status", "unknown")
        if status == "running":
            running_count += 1
        else:
            stopped_count += 1

        formatted_services.append(
            {
                "name": svc.get("name"),
                "status": status,
                "enabled": svc.get("enabled", True),
                "uptime": format_uptime(svc["uptime"]) if svc.get("uptime") else None,
            }
        )

    return {
        "server": server_name,
        "timestamp": datetime.now().isoformat(),
        "services": formatted_services,
        "summary": {
            "total": len(services),
            "running": running_count,
            "stopped": stopped_count,
        },
    }


def print_table(data: list[dict], headers: Optional[list[str]] = None) -> str:
    """
    生成表格格式的输出

    Args:
        data: 数据列表
        headers: 表头，为None时从数据中提取

    Returns:
        格式化的表格字符串
    """
    if not data:
        return "无数据"

    if headers is None:
        headers = list(data[0].keys())

    # 计算列宽
    widths = [len(str(h)) for h in headers]
    for row in data:
        for i, h in enumerate(headers):
            value = row.get(h, "")
            widths[i] = max(widths[i], len(str(value)))

    # 构建表格
    lines = []

    # 表头
    header_line = " | ".join(str(h).ljust(widths[i]) for i, h in enumerate(headers))
    lines.append(header_line)
    lines.append("-+-".join("-" * w for w in widths))

    # 数据行
    for row in data:
        line = " | ".join(str(row.get(h, "")).ljust(widths[i]) for i, h in enumerate(headers))
        lines.append(line)

    return "\n".join(lines)


def output_result(data: Any, output_format: str = "json", output_file: Optional[str] = None) -> str:
    """
    输出结果

    Args:
        data: 要输出的数据
        output_format: 输出格式 (json/table)
        output_file: 输出文件路径

    Returns:
        格式化后的输出字符串
    """
    import json

    if output_format == "json":
        # 处理dataclass对象
        if hasattr(data, "__dataclass_fields__"):
            from dataclasses import asdict

            output = json.dumps(asdict(data), ensure_ascii=False, indent=2)
        elif isinstance(data, dict):
            output = json.dumps(data, ensure_ascii=False, indent=2)
        elif isinstance(data, list):
            output = json.dumps(data, ensure_ascii=False, indent=2)
        else:
            output = str(data)
    else:
        output = str(data)

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output)

    return output


def generate_summary_report(results: dict, report_type: str) -> str:
    """
    生成摘要报告

    Args:
        results: 巡检结果
        report_type: 报告类型 (system/security/health)

    Returns:
        格式化的报告字符串
    """
    lines = []
    timestamp = format_timestamp()

    if report_type == "system":
        lines.append("=" * 50)
        lines.append(f"系统资源监控报告 - {timestamp}")
        lines.append("=" * 50)

        for server in results.get("servers", []):
            name = server.get("server", "Unknown")
            if "error" in server:
                lines.append(f"\n[{name}] 连接失败: {server['error']}")
                continue

            # 新格式数据
            cpu = server.get("cpu", {})
            memory = server.get("memory", {})
            disk = server.get("disk", {})

            lines.append(f"\n[{name}]")
            lines.append(f"  系统: {server.get('system', 'Unknown')} ({server.get('hostname', 'Unknown')})")
            lines.append(f"  运行时间: {server.get('uptime', 'Unknown')}")
            lines.append(f"  CPU: {cpu.get('usage', 0):.1f}% ({cpu.get('cores', 1)}核 - {cpu.get('model', 'Unknown')})")
            lines.append(f"  内存: {memory.get('percent', 0):.1f}% ({memory.get('used_mb', 0)}/{memory.get('total_mb', 0)} MB)")
            lines.append(f"  磁盘: {disk.get('percent', 0):.1f}% ({disk.get('used_human', '0')}/{disk.get('total_human', '0')})")

            # 资源统计
            resources = server.get("resources", {})
            if resources:
                lines.append(f"  资源: 网站{resources.get('sites', 0)}个, 数据库{resources.get('databases', 0)}个")

            alerts = server.get("alerts", [])
            if alerts:
                lines.append(f"  告警: {len(alerts)}条")
                for alert in alerts[:3]:
                    lines.append(f"    - [{alert['level']}] {alert['message']}")

        summary = results.get("summary", {})
        lines.append(f"\n汇总: 正常{summary.get('healthy', 0)}, 警告{summary.get('warning', 0)}, 异常{summary.get('critical', 0)}")

    elif report_type == "security":
        lines.append("=" * 50)
        lines.append(f"安全巡检报告 - {timestamp}")
        lines.append("=" * 50)

        for server in results.get("servers", []):
            name = server.get("server", "Unknown")
            risk = server.get("riskLevel", "unknown")

            risk_emoji = {"low": "✅", "medium": "🟡", "high": "🟠", "critical": "🔴"}.get(risk, "❓")
            lines.append(f"\n[{name}] 风险等级: {risk_emoji} {risk.upper()}")

            if "error" in server:
                lines.append(f"  检查失败: {server['error']}")
                continue

            ssh = server.get("ssh", {})
            if ssh:
                lines.append(f"  SSH端口: {ssh.get('port', 'N/A')}")

            firewall = server.get("firewall", {})
            if firewall:
                fw_status = "运行中" if firewall.get("status") == "running" else "已停止"
                lines.append(f"  防火墙: {fw_status}")

            alerts = server.get("alerts", [])
            if alerts:
                lines.append(f"  告警: {len(alerts)}条")

        summary = results.get("summary", {})
        lines.append(
            f"\n汇总: 低风险{summary.get('low', 0)}, 中风险{summary.get('medium', 0)}, "
            f"高风险{summary.get('high', 0)}, 严重{summary.get('critical', 0)}"
        )

    elif report_type == "health":
        lines.append("=" * 50)
        lines.append(f"健康检查报告 - {timestamp}")
        lines.append("=" * 50)

        for server in results.get("servers", []):
            name = server.get("server", "Unknown")
            status = server.get("overallStatus", "unknown")

            status_emoji = {"healthy": "✅", "warning": "🟡", "critical": "🔴"}.get(status, "❓")
            lines.append(f"\n[{name}] 状态: {status_emoji} {status.upper()}")

            if "error" in server:
                lines.append(f"  检查失败: {server['error']}")
                continue

            services = server.get("services", {})
            if services:
                lines.append(f"  服务: {services.get('running', 0)}/{services.get('total', 0)} 运行中")

            sites = server.get("sites", {})
            if sites:
                lines.append(f"  网站: {sites.get('running', 0)}/{sites.get('total', 0)} 运行中")

            databases = server.get("databases", {})
            if databases:
                lines.append(f"  数据库: {databases.get('total', 0)}个")

            alerts = server.get("alerts", [])
            if alerts:
                lines.append(f"  告警: {len(alerts)}条")

        summary = results.get("summary", {})
        lines.append(
            f"\n汇总: 健康{summary.get('healthy', 0)}, 警告{summary.get('warning', 0)}, "
            f"异常{summary.get('critical', 0)}"
        )

    lines.append("\n" + "=" * 50)
    return "\n".join(lines)
