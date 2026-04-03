#!/usr/bin/env python3
# coding: utf-8
"""
PHP 版本管理 CLI 工具
提供 PHP 版本查询、切换等功能
"""

import argparse
import sys
from pathlib import Path

# 兼容开发环境和发布环境的导入
_skill_root = Path(__file__).parent.parent
if (_skill_root / "bt_common").exists():
    sys.path.insert(0, str(_skill_root))
else:
    sys.path.insert(0, str(_skill_root.parent))

from bt_common.bt_client import BtClient, BtClientManager
from bt_common.config import get_servers


def get_client(server_name: str = None):
    """获取宝塔客户端"""
    if server_name:
        servers = get_servers()
        for server in servers:
            name = server.name if hasattr(server, 'name') else server.get('name')
            if name == server_name:
                config = {
                    'name': server.name if hasattr(server, 'name') else server.get('name'),
                    'host': server.host if hasattr(server, 'host') else server.get('host'),
                    'token': server.token if hasattr(server, 'token') else server.get('token'),
                    'timeout': server.timeout if hasattr(server, 'timeout') else server.get('timeout', 10000),
                    'verify_ssl': server.verify_ssl if hasattr(server, 'verify_ssl') else server.get('verify_ssl', True)
                }
                return BtClient(
                    name=config['name'],
                    host=config['host'],
                    token=config['token'],
                    timeout=config['timeout'],
                    verify_ssl=config['verify_ssl']
                )
        raise ValueError(f"未找到服务器：{server_name}")
    else:
        manager = BtClientManager()
        return manager.get_client()


def cmd_versions(args):
    """获取所有 PHP 版本列表"""
    client = get_client(args.server)

    endpoint = "/site?action=GetPHPVersion"
    params = {
        "s_type": 1,
        "all": 1
    }

    result = client.request(endpoint, params)

    if not result:
        print("获取 PHP 版本列表失败")
        return 1

    print("\n📊 PHP 版本列表\n")
    print(f"{'版本':<10} {'名称':<20} {'状态':<10}")
    print("-" * 45)

    # 按状态分组
    installed = []
    not_installed = []

    for v in result:
        version = v.get('version', '')
        name = v.get('name', '')
        status = v.get('status', False)

        if status:
            installed.append((version, name, status))
        else:
            not_installed.append((version, name, status))

    # 先显示已安装的
    for version, name, status in installed:
        print(f"{version:<10} {name:<20} ✅ 已安装")

    # 显示未安装的
    for version, name, status in not_installed:
        print(f"{version:<10} {name:<20} ❌ 未安装")

    return 0


def cmd_get(args):
    """获取站点当前 PHP 版本"""
    client = get_client(args.server)

    endpoint = "/site?action=GetSitePHPVersion"
    params = {
        "siteName": args.name
    }

    result = client.request(endpoint, params)

    if not result:
        print("获取 PHP 版本失败")
        return 1

    php_version = result.get('phpversion', 'unknown')

    # 版本名称映射
    version_names = {
        '00': '纯静态',
        'other': '自定义',
        '52': 'PHP 5.2',
        '53': 'PHP 5.3',
        '54': 'PHP 5.4',
        '55': 'PHP 5.5',
        '56': 'PHP 5.6',
        '70': 'PHP 7.0',
        '71': 'PHP 7.1',
        '72': 'PHP 7.2',
        '73': 'PHP 7.3',
        '74': 'PHP 7.4',
        '80': 'PHP 8.0',
        '81': 'PHP 8.1',
        '82': 'PHP 8.2',
        '83': 'PHP 8.3',
        '84': 'PHP 8.4',
    }

    version_name = version_names.get(php_version, f'PHP {php_version}')

    print(f"\n📊 站点 PHP 版本信息\n")
    print(f"站点：{args.name}")
    print(f"PHP 版本：{version_name} ({php_version})")

    # 其他信息
    if result.get('php_other'):
        print(f"自定义配置：{result.get('php_other')}")

    return 0


def cmd_set(args):
    """设置站点 PHP 版本"""
    client = get_client(args.server)

    endpoint = "/site?action=SetPHPVersion"

    if args.static:
        params = {
            "version": "00",
            "siteName": args.name
        }
        version_display = "纯静态"
    else:
        params = {
            "version": args.version,
            "siteName": args.name
        }
        version_display = f"PHP {args.version}"

    result = client.request(endpoint, params)

    if result.get('status'):
        print(f"✅ PHP 版本已切换：{args.name} -> {version_display}")
        return 0
    else:
        print(f"❌ PHP 版本切换失败：{result.get('msg', '未知错误')}")
        return 1


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='宝塔面板 PHP 版本管理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '-s', '--server',
        help='服务器名称（使用 bt-config 配置的名称）'
    )

    subparsers = parser.add_subparsers(dest='command', help='命令')

    # versions 命令
    versions_parser = subparsers.add_parser('versions', help='获取所有 PHP 版本列表')
    versions_parser.set_defaults(func=cmd_versions)

    # get 命令
    get_parser = subparsers.add_parser('get', help='获取站点当前 PHP 版本')
    get_parser.add_argument('-n', '--name', required=True, help='站点域名')
    get_parser.set_defaults(func=cmd_get)

    # set 命令
    set_parser = subparsers.add_parser('set', help='设置站点 PHP 版本')
    set_parser.add_argument('-n', '--name', required=True, help='站点域名')
    set_parser.add_argument('-v', '--version', help='PHP 版本号（如 82, 81, 74 等）')
    set_parser.add_argument('--static', action='store_true', help='设为纯静态站点')
    set_parser.set_defaults(func=cmd_set)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
