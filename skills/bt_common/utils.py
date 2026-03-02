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


def format_system_status(data: dict, server_name: str) -> dict:
    """
    格式化系统状态响应

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
        metrics: 格式化后的指标数据
        thresholds: 阈值配置

    Returns:
        告警列表
    """
    alerts = []

    cpu_threshold = thresholds.get("cpu", 80)
    memory_threshold = thresholds.get("memory", 85)
    disk_threshold = thresholds.get("disk", 90)

    cpu_usage = metrics.get("cpu", {}).get("usage", 0)
    if cpu_usage >= cpu_threshold:
        alerts.append(
            Alert(
                level="warning",
                type="cpu",
                message=f"CPU使用率过高: {cpu_usage}% (阈值: {cpu_threshold}%)",
                value=cpu_usage,
            )
        )

    mem_percent = metrics.get("memory", {}).get("percent", 0)
    if mem_percent >= memory_threshold:
        alerts.append(
            Alert(
                level="warning",
                type="memory",
                message=f"内存使用率过高: {mem_percent}% (阈值: {memory_threshold}%)",
                value=mem_percent,
            )
        )

    disk_percent = metrics.get("disk", {}).get("percent", 0)
    if disk_percent >= disk_threshold:
        alerts.append(
            Alert(
                level="critical",
                type="disk",
                message=f"磁盘使用率过高: {disk_percent}% (阈值: {disk_threshold}%)",
                value=disk_percent,
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

            metrics = server.get("metrics", {})
            cpu = metrics.get("cpu", {})
            memory = metrics.get("memory", {})
            disk = metrics.get("disk", {})

            lines.append(f"\n[{name}]")
            lines.append(f"  CPU: {cpu.get('usage', 0):.1f}% ({cpu.get('cores', 1)}核)")
            lines.append(f"  内存: {memory.get('percent', 0):.1f}% ({memory.get('used', 0):.1f}/{memory.get('total', 0):.1f} GB)")
            lines.append(f"  磁盘: {disk.get('percent', 0):.1f}% ({disk.get('used', 0):.1f}/{disk.get('total', 0):.1f} GB)")

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
