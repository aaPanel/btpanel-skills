#!/usr/bin/env python3
# /// script
# dependencies = [
#   "requests>=2.28",
#   "pyyaml>=6.0",
#   "rich>=13.0",
# ]
# ///
"""
安全事件巡检脚本
检查SSH登录、防火墙状态、可疑活动等
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

# 兼容开发环境和发布环境的导入
# 发布环境: skill/bt_common/ (脚本在 skill/scripts/)
# 开发环境: skills/bt_common/ (脚本在 skills/bt-security-check/scripts/)
_skill_root = Path(__file__).parent.parent  # 技能包根目录
_project_root = _skill_root.parent  # 项目根目录（开发环境为 skills 目录）

# 优先尝试发布环境（技能包根目录），然后尝试开发环境
if (_skill_root / "bt_common").exists():
    sys.path.insert(0, str(_skill_root))
else:
    sys.path.insert(0, str(_project_root))

from bt_common import BtClient, BtClientManager, load_config


@dataclass
class SecurityIssue:
    """安全问题"""

    level: str  # warning, critical
    message: str


@dataclass
class SSHAnalysis:
    """SSH分析结果"""

    status: str = "safe"  # safe, warning, critical
    issues: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)


def analyze_ssh_security(ssh_info: dict) -> SSHAnalysis:
    """
    分析SSH安全状态

    Args:
        ssh_info: SSH信息

    Returns:
        SSH分析结果
    """
    analysis = SSHAnalysis()

    # 检查SSH端口
    port = ssh_info.get("port", 22)
    if port == 22:
        analysis.issues.append(
            SecurityIssue(level="warning", message="SSH使用默认端口22，建议修改为非常规端口")
        )
        analysis.status = "warning"

    # 检查是否允许密码登录
    password_auth = ssh_info.get("PasswordAuthentication") or ssh_info.get("password_auth")
    if password_auth in (True, "yes"):
        analysis.issues.append(
            SecurityIssue(level="warning", message="SSH允许密码登录，建议禁用并使用密钥认证")
        )
        analysis.status = "warning"

    # 检查是否允许root登录
    root_login = ssh_info.get("PermitRootLogin") or ssh_info.get("root_login")
    if root_login in (True, "yes"):
        analysis.issues.append(
            SecurityIssue(level="warning", message="SSH允许root直接登录，建议禁用")
        )
        analysis.status = "warning"

    # 添加建议
    analysis.recommendations = [
        "定期检查SSH登录日志",
        "使用fail2ban防止暴力破解",
    ]

    return analysis


@dataclass
class FirewallAnalysis:
    """防火墙分析结果"""

    status: str = "safe"
    issues: list = field(default_factory=list)
    rules: list = field(default_factory=list)


def analyze_firewall(firewall_status: dict) -> FirewallAnalysis:
    """
    分析防火墙状态

    Args:
        firewall_status: 防火墙状态

    Returns:
        防火墙分析结果
    """
    analysis = FirewallAnalysis()

    # 检查防火墙是否启用
    status = firewall_status.get("status") or firewall_status.get("state")
    enabled = firewall_status.get("enabled", True)

    if status not in ("running", "active") and not enabled:
        analysis.issues.append(
            SecurityIssue(level="critical", message="防火墙未启用，服务器暴露在风险中")
        )
        analysis.status = "critical"

    # 解析规则数量
    if firewall_status.get("rules"):
        analysis.rules = firewall_status["rules"]

    return analysis


@dataclass
class SecurityLogAnalysis:
    """安全日志分析结果"""

    failed_logins: list = field(default_factory=list)
    suspicious_ips: list = field(default_factory=list)
    recent_alerts: list = field(default_factory=list)


def extract_ip(log_text: str) -> Optional[str]:
    """从日志文本中提取IP"""
    if not log_text:
        return None
    match = re.search(r"(\d{1,3}\.){3}\d{1,3}", log_text)
    return match.group(0) if match else None


def extract_user(log_text: str) -> Optional[str]:
    """从日志文本中提取用户名"""
    if not log_text:
        return None
    match = re.search(r"user\s+(\w+)", log_text, re.IGNORECASE)
    return match.group(1) if match else None


def analyze_security_logs(logs: list) -> SecurityLogAnalysis:
    """
    分析安全日志

    Args:
        logs: 安全日志列表

    Returns:
        安全日志分析结果
    """
    analysis = SecurityLogAnalysis()
    suspicious_ips_map: dict[str, int] = {}

    if not logs or not isinstance(logs, True):
        return analysis

    # 统计失败登录
    for log in logs:
        log_type = log.get("type", "")
        log_content = log.get("log", "") or log.get("message", "")

        if log_type == "login_failed" or "Failed" in str(log_content):
            ip = log.get("ip") or extract_ip(str(log_content))
            if ip:
                suspicious_ips_map[ip] = suspicious_ips_map.get(ip, 0) + 1
                analysis.failed_logins.append(
                    {
                        "ip": ip,
                        "time": log.get("time") or log.get("addtime"),
                        "user": log.get("user") or extract_user(str(log_content)),
                    }
                )

    # 转换为计数数组并排序
    analysis.suspicious_ips = sorted(
        [{"ip": ip, "count": count} for ip, count in suspicious_ips_map.items()],
        key=lambda x: x["count"],
        reverse=True,
    )

    # 生成告警
    for ip_data in analysis.suspicious_ips:
        ip = ip_data["ip"]
        count = ip_data["count"]
        if count >= 5:
            analysis.recent_alerts.append(
                {
                    "level": "critical" if count >= 10 else "warning",
                    "message": f"IP {ip} 有 {count} 次失败登录尝试，可能存在暴力破解",
                    "ip": ip,
                    "count": count,
                }
            )

    return analysis


def check_server_security(client: BtClient) -> dict:
    """
    检查单个服务器的安全状态

    Args:
        client: 宝塔客户端

    Returns:
        安全检查结果
    """
    result = {
        "server": client.name,
        "timestamp": datetime.now().isoformat(),
        "ssh": None,
        "firewall": None,
        "logs": None,
        "alerts": [],
        "riskLevel": "low",
    }

    # 获取SSH信息
    try:
        ssh_info = client.get_ssh_info()
        ssh_analysis = analyze_ssh_security(ssh_info)
        result["ssh"] = {
            "port": ssh_info.get("port", 22),
            "status": ssh_info.get("status", "unknown"),
            "passwordAuth": ssh_info.get("PasswordAuthentication", "unknown"),
            "rootLogin": ssh_info.get("PermitRootLogin", "unknown"),
            "analysis": {
                "status": ssh_analysis.status,
                "issues": [{"level": i.level, "message": i.message} for i in ssh_analysis.issues],
                "recommendations": ssh_analysis.recommendations,
            },
        }
        result["alerts"].extend([{"level": i.level, "type": "ssh", "message": i.message} for i in ssh_analysis.issues])
    except Exception as e:
        result["ssh"] = {"error": str(e)}

    # 获取防火墙状态
    try:
        firewall_status = client.get_firewall_status()
        firewall_analysis = analyze_firewall(firewall_status)
        result["firewall"] = {
            "status": firewall_status.get("status") or firewall_status.get("state", "unknown"),
            "enabled": firewall_status.get("enabled", True),
            "analysis": {
                "status": firewall_analysis.status,
                "issues": [{"level": i.level, "message": i.message} for i in firewall_analysis.issues],
            },
        }
        result["alerts"].extend(
            [{"level": i.level, "type": "firewall", "message": i.message} for i in firewall_analysis.issues]
        )
    except Exception as e:
        result["firewall"] = {"error": str(e)}

    # 获取安全日志
    try:
        logs_data = client.get_security_logs(1, 50)
        logs_list = logs_data.get("data", logs_data) if isinstance(logs_data, dict) else logs_data
        logs_analysis = analyze_security_logs(logs_list if isinstance(logs_list, list) else [])
        result["logs"] = {
            "failedLogins": logs_analysis.failed_logins[:10],
            "suspiciousIps": logs_analysis.suspicious_ips[:5],
            "recentAlerts": logs_analysis.recent_alerts,
        }
        result["alerts"].extend(logs_analysis.recent_alerts)
    except Exception as e:
        result["logs"] = {"error": str(e)}

    # 计算整体风险等级
    critical_count = sum(1 for a in result["alerts"] if a.get("level") == "critical")
    warning_count = sum(1 for a in result["alerts"] if a.get("level") == "warning")

    if critical_count > 0:
        result["riskLevel"] = "critical"
    elif warning_count > 2:
        result["riskLevel"] = "high"
    elif warning_count > 0:
        result["riskLevel"] = "medium"

    return result


def run_security_check(manager: BtClientManager, server: Optional[str] = None) -> dict:
    """
    执行安全巡检

    Args:
        manager: 客户端管理器
        server: 指定服务器名称

    Returns:
        巡检结果
    """
    # 单个服务器
    if server:
        client = manager.get_client(server)
        return check_server_security(client)

    # 所有服务器
    all_clients = manager.get_all_clients()
    results = {
        "timestamp": datetime.now().isoformat(),
        "servers": [],
        "summary": {"total": len(all_clients), "low": 0, "medium": 0, "high": 0, "critical": 0},
    }

    for name, client in all_clients.items():
        try:
            security_result = check_server_security(client)
            results["servers"].append(security_result)
            results["summary"][security_result["riskLevel"]] += 1
        except Exception as e:
            results["servers"].append(
                {
                    "server": name,
                    "error": str(e),
                    "riskLevel": "critical",
                    "alerts": [{"level": "critical", "message": str(e)}],
                }
            )
            results["summary"]["critical"] += 1

    return results


def print_table_output(results: dict):
    """打印表格格式输出"""
    try:
        from rich.console import Console
        from rich.table import Table

        console = Console()

        if "servers" in results:
            # 多服务器模式
            table = Table(title="安全巡检报告")
            table.add_column("服务器", style="cyan")
            table.add_column("风险等级", style="bold")
            table.add_column("SSH端口", style="green")
            table.add_column("防火墙", style="yellow")
            table.add_column("告警数", style="red")

            risk_colors = {"low": "green", "medium": "yellow", "high": "orange", "critical": "red"}

            for server in results["servers"]:
                risk = server.get("riskLevel", "unknown")
                risk_color = risk_colors.get(risk, "white")

                if "error" in server:
                    table.add_row(
                        server["server"],
                        f"[red]错误[/red]",
                        "-",
                        "-",
                        "-",
                    )
                    continue

                ssh = server.get("ssh", {})
                firewall = server.get("firewall", {})

                fw_status = "运行中" if firewall.get("status") == "running" else "已停止"

                alerts_count = len(server.get("alerts", []))

                table.add_row(
                    server["server"],
                    f"[{risk_color}]{risk.upper()}[/{risk_color}]",
                    str(ssh.get("port", "N/A")),
                    fw_status,
                    str(alerts_count),
                )

            console.print(table)

            # 打印汇总
            summary = results.get("summary", {})
            console.print(
                f"\n汇总: [green]低风险{summary.get('low', 0)}[/green], "
                f"[yellow]中风险{summary.get('medium', 0)}[/yellow], "
                f"[orange]高风险{summary.get('high', 0)}[/orange], "
                f"[red]严重{summary.get('critical', 0)}[/red]"
            )

            # 打印详细告警
            for server in results["servers"]:
                alerts = server.get("alerts", [])
                if alerts:
                    console.print(f"\n[bold]{server['server']} 告警详情:[/bold]")
                    for alert in alerts[:5]:
                        level = alert.get("level", "warning")
                        color = "red" if level == "critical" else "yellow"
                        console.print(f"  [{color}]• {alert.get('message', '')}[/{color}]")
        else:
            # 单服务器模式
            console.print(f"\n[bold]服务器: {results.get('server', 'Unknown')}[/bold]")
            console.print(f"风险等级: {results.get('riskLevel', 'unknown').upper()}\n")

            # SSH信息
            ssh = results.get("ssh", {})
            if ssh and "error" not in ssh:
                console.print("[bold]SSH配置:[/bold]")
                console.print(f"  端口: {ssh.get('port', 'N/A')}")
                console.print(f"  状态: {ssh.get('status', 'unknown')}")
                analysis = ssh.get("analysis", {})
                if analysis.get("issues"):
                    console.print("  问题:")
                    for issue in analysis["issues"]:
                        color = "red" if issue["level"] == "critical" else "yellow"
                        console.print(f"    [{color}]• {issue['message']}[/{color}]")

            # 防火墙信息
            firewall = results.get("firewall", {})
            if firewall and "error" not in firewall:
                console.print("\n[bold]防火墙:[/bold]")
                console.print(f"  状态: {firewall.get('status', 'unknown')}")

            # 可疑IP
            logs = results.get("logs", {})
            if logs and logs.get("suspiciousIps"):
                console.print("\n[bold]可疑IP:[/bold]")
                for ip_data in logs["suspiciousIps"][:5]:
                    console.print(f"  • {ip_data['ip']}: {ip_data['count']}次失败登录")

    except ImportError:
        print("请安装rich库以使用表格输出: pip install rich")
        print(json.dumps(results, ensure_ascii=False, indent=2))


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="宝塔面板安全巡检",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 检查所有服务器安全状态
  %(prog)s

  # 检查指定服务器
  %(prog)s --server prod-01

  # JSON格式输出
  %(prog)s --format json
        """,
    )
    parser.add_argument("--server", "-s", help="指定服务器名称")
    parser.add_argument("--format", "-f", choices=["json", "table"], default="json", help="输出格式")
    parser.add_argument("--output", "-o", help="输出文件路径")
    parser.add_argument("--config", "-c", help="配置文件路径")

    args = parser.parse_args()

    # 初始化客户端管理器
    manager = BtClientManager()

    try:
        manager.load_config(args.config)
    except FileNotFoundError as e:
        print(f"错误: {e}", file=sys.stderr)
        print("请设置 BT_CONFIG_PATH 环境变量或创建配置文件", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"加载配置失败: {e}", file=sys.stderr)
        sys.exit(1)

    if not manager.get_all_clients():
        print("错误: 没有配置任何服务器", file=sys.stderr)
        sys.exit(1)

    # 执行安全检查
    try:
        results = run_security_check(manager, args.server)
    except KeyError as e:
        print(f"错误: 未找到服务器 {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"安全检查失败: {e}", file=sys.stderr)
        sys.exit(1)

    # 输出结果
    if args.format == "table":
        print_table_output(results)
    else:
        output = json.dumps(results, ensure_ascii=False, indent=2)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
            print(f"结果已保存到: {args.output}")
        else:
            print(output)


if __name__ == "__main__":
    main()
