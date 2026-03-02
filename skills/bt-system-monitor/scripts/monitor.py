#!/usr/bin/env python3
# /// script
# dependencies = [
#   "requests>=2.28",
#   "pyyaml>=6.0",
#   "rich>=13.0",
# ]
# ///
"""
系统资源监控脚本
监控CPU、内存、磁盘和网络使用情况
"""

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Optional

# 兼容开发环境和发布环境的导入
# 发布环境: skill/bt_common/ (脚本在 skill/scripts/)
# 开发环境: skills/bt_common/ (脚本在 skills/bt-system-monitor/scripts/)
_skill_root = Path(__file__).parent.parent  # 技能包根目录
_project_root = _skill_root.parent  # 项目根目录（开发环境为 skills 目录）

# 优先尝试发布环境（技能包根目录），然后尝试开发环境
if (_skill_root / "bt_common").exists():
    sys.path.insert(0, str(_skill_root))
else:
    sys.path.insert(0, str(_project_root))

from bt_common import (
    BtClient,
    BtClientManager,
    check_thresholds,
    format_system_status,
    format_uptime,
    load_config,
)


def get_server_system_status(client: BtClient, thresholds: dict) -> dict:
    """
    获取单个服务器的系统状态

    Args:
        client: 宝塔客户端
        thresholds: 告警阈值配置

    Returns:
        系统状态信息
    """
    # 获取系统状态
    status_data = client.get_system_status()

    # 格式化数据
    formatted = format_system_status(status_data, client.name)

    # 检查告警
    alerts = check_thresholds(formatted["metrics"], thresholds)

    result = formatted if isinstance(formatted, dict) else asdict(formatted)
    result["alerts"] = [asdict(a) if hasattr(a, "__dataclass_fields__") else a for a in alerts]
    return result


def get_server_network_info(client: BtClient) -> dict:
    """
    获取网络信息

    Args:
        client: 宝塔客户端

    Returns:
        网络信息
    """
    from datetime import datetime

    net_data = client.get_network_info()

    return {
        "server": client.name,
        "timestamp": datetime.now().isoformat(),
        "network": {
            "up": net_data.get("up", 0),
            "down": net_data.get("down", 0),
            "upTotal": net_data.get("up_total", 0),
            "downTotal": net_data.get("down_total", 0),
            "interfaces": net_data.get("interfaces", []),
        },
    }


def run_monitor(manager: BtClientManager, server: Optional[str] = None, include_network: bool = False) -> dict:
    """
    执行系统监控

    Args:
        manager: 客户端管理器
        server: 指定服务器名称
        include_network: 是否包含网络信息

    Returns:
        监控结果
    """
    from datetime import datetime

    thresholds = manager.get_global_config().get("thresholds", {"cpu": 80, "memory": 85, "disk": 90})

    # 单个服务器
    if server:
        client = manager.get_client(server)
        status = get_server_system_status(client, thresholds)

        if include_network:
            status["network"] = get_server_network_info(client)["network"]

        return status

    # 所有服务器
    all_clients = manager.get_all_clients()
    results = {
        "timestamp": datetime.now().isoformat(),
        "servers": [],
        "summary": {"total": len(all_clients), "healthy": 0, "warning": 0, "critical": 0},
    }

    for name, client in all_clients.items():
        try:
            status = get_server_system_status(client, thresholds)

            if include_network:
                status["network"] = get_server_network_info(client)["network"]

            results["servers"].append(status)

            # 统计健康状态
            alerts = status.get("alerts", [])
            if not alerts:
                results["summary"]["healthy"] += 1
            else:
                has_critical = any(a.get("level") == "critical" for a in alerts)
                if has_critical:
                    results["summary"]["critical"] += 1
                else:
                    results["summary"]["warning"] += 1

        except Exception as e:
            results["servers"].append(
                {
                    "server": name,
                    "error": str(e),
                    "alerts": [{"level": "critical", "type": "connection", "message": str(e)}],
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
            table = Table(title="系统资源监控")
            table.add_column("服务器", style="cyan")
            table.add_column("CPU", style="green")
            table.add_column("内存", style="yellow")
            table.add_column("磁盘", style="red")
            table.add_column("状态", style="bold")

            for server in results["servers"]:
                if "error" in server:
                    table.add_row(
                        server["server"],
                        "-",
                        "-",
                        "-",
                        "[red]连接失败[/red]",
                    )
                    continue

                metrics = server.get("metrics", {})
                cpu = metrics.get("cpu", {})
                memory = metrics.get("memory", {})
                disk = metrics.get("disk", {})

                # 确定状态颜色
                alerts = server.get("alerts", [])
                if not alerts:
                    status = "[green]正常[/green]"
                elif any(a.get("level") == "critical" for a in alerts):
                    status = "[red]异常[/red]"
                else:
                    status = "[yellow]警告[/yellow]"

                table.add_row(
                    server["server"],
                    f"{cpu.get('usage', 0):.1f}%",
                    f"{memory.get('percent', 0):.1f}%",
                    f"{disk.get('percent', 0):.1f}%",
                    status,
                )

            console.print(table)

            # 打印汇总
            summary = results.get("summary", {})
            console.print(
                f"\n汇总: [green]正常{summary.get('healthy', 0)}[/green], "
                f"[yellow]警告{summary.get('warning', 0)}[/yellow], "
                f"[red]异常{summary.get('critical', 0)}[/red]"
            )
        else:
            # 单服务器模式
            table = Table(title=f"服务器: {results.get('server', 'Unknown')}")
            table.add_column("指标", style="cyan")
            table.add_column("值", style="green")

            metrics = results.get("metrics", {})
            cpu = metrics.get("cpu", {})
            memory = metrics.get("memory", {})
            disk = metrics.get("disk", {})
            system = metrics.get("system", {})

            table.add_row("CPU使用率", f"{cpu.get('usage', 0):.1f}%")
            table.add_row("CPU核心", str(cpu.get("cores", 1)))
            table.add_row("内存使用", f"{memory.get('used', 0):.1f}/{memory.get('total', 0):.1f} GB ({memory.get('percent', 0):.1f}%)")
            table.add_row("磁盘使用", f"{disk.get('used', 0):.1f}/{disk.get('total', 0):.1f} GB ({disk.get('percent', 0):.1f}%)")
            table.add_row("主机名", system.get("hostname", "Unknown"))
            table.add_row("运行时间", system.get("uptime", "Unknown"))

            console.print(table)

            # 打印告警
            alerts = results.get("alerts", [])
            if alerts:
                console.print("\n[bold yellow]告警:[/bold yellow]")
                for alert in alerts:
                    level = alert.get("level", "warning")
                    color = "red" if level == "critical" else "yellow"
                    console.print(f"  [{color}]{alert.get('message', '')}[/{color}]")

    except ImportError:
        # 如果没有rich库，使用简单输出
        print("请安装rich库以使用表格输出: pip install rich")
        print(json.dumps(results, ensure_ascii=False, indent=2))


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="宝塔面板系统资源监控",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 监控所有服务器
  %(prog)s

  # 监控指定服务器
  %(prog)s --server prod-01

  # JSON格式输出
  %(prog)s --format json

  # 包含网络信息
  %(prog)s --include-network
        """,
    )
    parser.add_argument("--server", "-s", help="指定服务器名称")
    parser.add_argument("--format", "-f", choices=["json", "table"], default="json", help="输出格式")
    parser.add_argument("--output", "-o", help="输出文件路径")
    parser.add_argument("--include-network", "-n", action="store_true", help="包含网络信息")
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

    # 执行监控
    try:
        results = run_monitor(manager, args.server, args.include_network)
    except KeyError as e:
        print(f"错误: 未找到服务器 {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"监控失败: {e}", file=sys.stderr)
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
