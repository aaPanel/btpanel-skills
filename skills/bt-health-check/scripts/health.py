#!/usr/bin/env python3
# /// script
# dependencies = [
#   "requests>=2.28",
#   "pyyaml>=6.0",
#   "rich>=13.0",
# ]
# ///
"""
服务健康检查脚本
检查网站、数据库、服务等运行状态
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# 兼容开发环境和发布环境的导入
# 发布环境: skill/bt_common/ (脚本在 skill/scripts/)
# 开发环境: skills/bt_common/ (脚本在 skills/bt-health-check/scripts/)
_skill_root = Path(__file__).parent.parent  # 技能包根目录
_project_root = _skill_root.parent  # 项目根目录（开发环境为 skills 目录）

# 优先尝试发布环境（技能包根目录），然后尝试开发环境
if (_skill_root / "bt_common").exists():
    sys.path.insert(0, str(_skill_root))
else:
    sys.path.insert(0, str(_project_root))

from bt_common import BtClient, BtClientManager, format_bytes, format_uptime, load_config


# 常见服务定义
COMMON_SERVICES = {
    "nginx": {"name": "Nginx", "type": "web"},
    "apache": {"name": "Apache", "type": "web"},
    "mysql": {"name": "MySQL", "type": "database"},
    "mariadb": {"name": "MariaDB", "type": "database"},
    "redis": {"name": "Redis", "type": "cache"},
    "memcached": {"name": "Memcached", "type": "cache"},
    "php": {"name": "PHP-FPM", "type": "runtime"},
    "docker": {"name": "Docker", "type": "container"},
    "supervisor": {"name": "Supervisor", "type": "process"},
}

# 关键服务列表
CRITICAL_SERVICES = ["nginx", "apache", "mysql", "mariadb", "redis"]


def check_service_health(client: BtClient, service_name: str) -> dict:
    """
    检查单个服务的健康状态

    Args:
        client: 宝塔客户端
        service_name: 服务名称

    Returns:
        服务健康状态
    """
    try:
        service_list = client.get_service_list()
        service = None

        for s in service_list:
            if s.get("name", "").lower() == service_name.lower():
                service = s
                break

        if not service:
            return {"name": service_name, "status": "not_found", "message": "服务未找到"}

        service_info = COMMON_SERVICES.get(service_name.lower(), {})
        status = service.get("status", "unknown")

        return {
            "name": service_name,
            "displayName": service_info.get("name", service_name),
            "type": service_info.get("type", "unknown"),
            "status": status,
            "running": status == "running",
            "enabled": service.get("enabled", True),
            "uptime": service.get("uptime"),
            "memory": service.get("memory"),
            "cpu": service.get("cpu"),
        }
    except Exception as e:
        return {"name": service_name, "status": "error", "error": str(e)}


def check_sites_health(client: BtClient) -> dict:
    """
    检查网站健康状态

    Args:
        client: 宝塔客户端

    Returns:
        网站健康状态
    """
    result = {"total": 0, "running": 0, "stopped": 0, "sites": []}

    try:
        sites_data = client.get_site_list()

        if not sites_data or not isinstance(sites_data, list):
            return result

        result["total"] = len(sites_data)

        for site in sites_data:
            site_info = {
                "name": site.get("name") or site.get("siteName", "Unknown"),
                "domain": site.get("name") or site.get("domain", ""),
                "status": site.get("status", "unknown"),
                "ssl": site.get("ssl") in (True, "1", 1),
                "sslExpiry": site.get("ssl_expiry") or site.get("sslEndDate"),
                "path": site.get("path"),
            }

            # 判断运行状态
            if site.get("status") in ("running", "1", 1):
                result["running"] += 1
                site_info["status"] = "running"
            else:
                result["stopped"] += 1
                site_info["status"] = "stopped"

            # 检查SSL证书是否即将过期
            if site_info["ssl"] and site_info["sslExpiry"]:
                try:
                    expiry_date = datetime.fromisoformat(str(site_info["sslExpiry"]).replace("Z", "+00:00"))
                    days_left = (expiry_date - datetime.now(expiry_date.tzinfo)).days
                    site_info["sslDaysLeft"] = days_left

                    if days_left <= 7:
                        site_info["sslAlert"] = {
                            "level": "critical",
                            "message": f"SSL证书将在{days_left}天后过期",
                        }
                    elif days_left <= 30:
                        site_info["sslAlert"] = {
                            "level": "warning",
                            "message": f"SSL证书将在{days_left}天后过期",
                        }
                except (ValueError, TypeError):
                    pass

            result["sites"].append(site_info)

    except Exception as e:
        result["error"] = str(e)

    return result


def check_databases_health(client: BtClient) -> dict:
    """
    检查数据库健康状态

    Args:
        client: 宝塔客户端

    Returns:
        数据库健康状态
    """
    result = {"total": 0, "databases": [], "sizeTotal": 0}

    try:
        db_data = client.get_database_list()

        if not db_data or not isinstance(db_data, list):
            return result

        result["total"] = len(db_data)

        for db in db_data:
            db_info = {
                "name": db.get("name", "Unknown"),
                "type": db.get("type", "mysql"),
                "size": db.get("size", 0),
                "sizeFormatted": format_bytes(db.get("size", 0)),
            }
            result["sizeTotal"] += db_info["size"]
            result["databases"].append(db_info)

        result["sizeTotalFormatted"] = format_bytes(result["sizeTotal"])

    except Exception as e:
        result["error"] = str(e)

    return result


def check_server_health(client: BtClient, check_services: bool = True, check_sites: bool = True, check_databases: bool = True) -> dict:
    """
    检查单个服务器的健康状态

    Args:
        client: 宝塔客户端
        check_services: 是否检查服务
        check_sites: 是否检查网站
        check_databases: 是否检查数据库

    Returns:
        健康检查结果
    """
    result = {
        "server": client.name,
        "timestamp": datetime.now().isoformat(),
        "services": None,
        "sites": None,
        "databases": None,
        "alerts": [],
        "overallStatus": "healthy",
    }

    # 检查服务状态
    if check_services:
        try:
            service_list = client.get_service_list()
            services = []

            for service in service_list if isinstance(service_list, list) else []:
                svc_name = service.get("name", "")
                svc_status = service.get("status", "unknown")

                services.append(
                    {
                        "name": svc_name,
                        "status": svc_status,
                        "running": svc_status == "running",
                        "uptime": format_uptime(service["uptime"]) if service.get("uptime") else None,
                    }
                )

                # 检查关键服务是否停止
                if svc_status != "running" and svc_name.lower() in CRITICAL_SERVICES:
                    result["alerts"].append(
                        {
                            "level": "critical",
                            "type": "service",
                            "message": f"关键服务 {svc_name} 已停止",
                            "service": svc_name,
                        }
                    )

            result["services"] = {
                "total": len(services),
                "running": sum(1 for s in services if s["running"]),
                "stopped": sum(1 for s in services if not s["running"]),
                "list": services,
            }
        except Exception as e:
            result["services"] = {"error": str(e)}

    # 检查网站状态
    if check_sites:
        result["sites"] = check_sites_health(client)

        # 检查SSL告警
        for site in result["sites"].get("sites", []):
            if site.get("sslAlert"):
                result["alerts"].append(
                    {
                        "level": site["sslAlert"]["level"],
                        "type": "ssl",
                        "message": f"{site['name']}: {site['sslAlert']['message']}",
                        "site": site["name"],
                    }
                )

    # 检查数据库状态
    if check_databases:
        result["databases"] = check_databases_health(client)

    # 计算整体状态
    critical_alerts = [a for a in result["alerts"] if a.get("level") == "critical"]
    if critical_alerts:
        result["overallStatus"] = "critical"
    elif result["alerts"]:
        result["overallStatus"] = "warning"

    return result


def run_health_check(
    manager: BtClientManager,
    server: Optional[str] = None,
    check_services: bool = True,
    check_sites: bool = True,
    check_databases: bool = True,
) -> dict:
    """
    执行健康检查

    Args:
        manager: 客户端管理器
        server: 指定服务器名称
        check_services: 是否检查服务
        check_sites: 是否检查网站
        check_databases: 是否检查数据库

    Returns:
        健康检查结果
    """
    # 单个服务器
    if server:
        client = manager.get_client(server)
        return check_server_health(client, check_services, check_sites, check_databases)

    # 所有服务器
    all_clients = manager.get_all_clients()
    results = {
        "timestamp": datetime.now().isoformat(),
        "servers": [],
        "summary": {"total": len(all_clients), "healthy": 0, "warning": 0, "critical": 0},
    }

    for name, client in all_clients.items():
        try:
            health_result = check_server_health(client, check_services, check_sites, check_databases)
            results["servers"].append(health_result)
            results["summary"][health_result["overallStatus"]] += 1
        except Exception as e:
            results["servers"].append(
                {
                    "server": name,
                    "error": str(e),
                    "overallStatus": "critical",
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
            table = Table(title="服务健康检查报告")
            table.add_column("服务器", style="cyan")
            table.add_column("状态", style="bold")
            table.add_column("服务", style="green")
            table.add_column("网站", style="yellow")
            table.add_column("数据库", style="blue")
            table.add_column("告警", style="red")

            status_colors = {"healthy": "green", "warning": "yellow", "critical": "red"}

            for server in results["servers"]:
                status = server.get("overallStatus", "unknown")
                status_color = status_colors.get(status, "white")

                if "error" in server:
                    table.add_row(
                        server["server"],
                        "[red]错误[/red]",
                        "-",
                        "-",
                        "-",
                        "-",
                    )
                    continue

                services = server.get("services", {})
                sites = server.get("sites", {})
                databases = server.get("databases", {})

                services_str = f"{services.get('running', 0)}/{services.get('total', 0)}" if services else "N/A"
                sites_str = f"{sites.get('running', 0)}/{sites.get('total', 0)}" if sites else "N/A"
                db_str = str(databases.get("total", 0)) if databases else "N/A"

                table.add_row(
                    server["server"],
                    f"[{status_color}]{status.upper()}[/{status_color}]",
                    services_str,
                    sites_str,
                    db_str,
                    str(len(server.get("alerts", []))),
                )

            console.print(table)

            # 打印汇总
            summary = results.get("summary", {})
            console.print(
                f"\n汇总: [green]健康{summary.get('healthy', 0)}[/green], "
                f"[yellow]警告{summary.get('warning', 0)}[/yellow], "
                f"[red]异常{summary.get('critical', 0)}[/red]"
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
            status = results.get("overallStatus", "unknown")
            status_color = {"healthy": "green", "warning": "yellow", "critical": "red"}.get(status, "white")
            console.print(f"状态: [{status_color}]{status.upper()}[/{status_color}]\n")

            # 服务信息
            services = results.get("services", {})
            if services and "error" not in services:
                console.print("[bold]服务状态:[/bold]")
                console.print(f"  运行中: {services.get('running', 0)}/{services.get('total', 0)}")
                for svc in services.get("list", [])[:5]:
                    status_str = "[green]运行中[/green]" if svc["running"] else "[red]已停止[/red]"
                    console.print(f"  • {svc['name']}: {status_str}")

            # 网站信息
            sites = results.get("sites", {})
            if sites and "error" not in sites:
                console.print("\n[bold]网站状态:[/bold]")
                console.print(f"  运行中: {sites.get('running', 0)}/{sites.get('total', 0)}")

            # 数据库信息
            databases = results.get("databases", {})
            if databases and "error" not in databases:
                console.print("\n[bold]数据库:[/bold]")
                console.print(f"  数量: {databases.get('total', 0)}")
                console.print(f"  总大小: {databases.get('sizeTotalFormatted', 'N/A')}")

            # 告警
            alerts = results.get("alerts", [])
            if alerts:
                console.print("\n[bold red]告警:[/bold red]")
                for alert in alerts:
                    level = alert.get("level", "warning")
                    color = "red" if level == "critical" else "yellow"
                    console.print(f"  [{color}]• {alert.get('message', '')}[/{color}]")

    except ImportError:
        print("请安装rich库以使用表格输出: pip install rich")
        print(json.dumps(results, ensure_ascii=False, indent=2))


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="宝塔面板服务健康检查",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 检查所有服务器健康状态
  %(prog)s

  # 检查指定服务器
  %(prog)s --server prod-01

  # 只检查服务
  %(prog)s --check-services

  # JSON格式输出
  %(prog)s --format json
        """,
    )
    parser.add_argument("--server", "-s", help="指定服务器名称")
    parser.add_argument("--format", "-f", choices=["json", "table"], default="json", help="输出格式")
    parser.add_argument("--output", "-o", help="输出文件路径")
    parser.add_argument("--check-services", action="store_true", help="只检查服务状态")
    parser.add_argument("--check-sites", action="store_true", help="只检查网站状态")
    parser.add_argument("--check-databases", action="store_true", help="只检查数据库状态")
    parser.add_argument("--config", "-c", help="配置文件路径")

    args = parser.parse_args()

    # 确定检查项目
    if args.check_services or args.check_sites or args.check_databases:
        check_services = args.check_services
        check_sites = args.check_sites
        check_databases = args.check_databases
    else:
        check_services = True
        check_sites = True
        check_databases = True

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

    # 执行健康检查
    try:
        results = run_health_check(manager, args.server, check_services, check_sites, check_databases)
    except KeyError as e:
        print(f"错误: 未找到服务器 {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"健康检查失败: {e}", file=sys.stderr)
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
