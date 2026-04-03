#!/usr/bin/env python3
# coding: utf-8
"""
域名管理 CLI 工具
提供域名添加、删除、查询等功能
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


def cmd_list(args):
    """列出站点的所有域名"""
    client = get_client(args.server)

    # 先获取站点信息获取站点 ID（不使用 search 参数，避免搜索问题）
    endpoint = "/datalist/data/get_data_list"
    params = {
        "table": "sites",
        "type": "-1",
        "p": 1,
        "limit": 100
    }

    result = client.request(endpoint, params)
    data = result.get('data', [])

    # 查找匹配的站点（支持 ID 或域名匹配）
    site_id = None
    for s in data:
        if str(s.get('id')) == str(args.name) or s.get('name') == args.name:
            site_id = s.get('id')
            break

    if not site_id:
        print(f"未找到站点：{args.name}")
        return 1

    # 获取域名列表
    endpoint = "/data?action=getData"
    params = {
        "table": "domain",
        "list": "True",
        "search": site_id
    }

    result = client.request(endpoint, params)

    # 检查 API 返回结果
    if not result:
        print("获取域名列表失败")
        return 1

    # 处理 API 错误响应
    if isinstance(result, dict) and result.get('status') is False:
        print(f"获取域名列表失败：{result.get('msg', '未知错误')}")
        return 1

    print(f"\n📊 站点域名列表：{args.name}\n")
    print(f"{'ID':<8} {'域名':<40} {'端口':<10} {'添加时间':<20}")
    print("-" * 85)

    for domain in result:
        domain_id = domain.get('id', 0)
        name = domain.get('cn_name', domain.get('name', 'unknown'))
        port = domain.get('port', 80)
        addtime = domain.get('addtime', 'unknown')

        print(f"{domain_id:<8} {name:<40} {port:<10} {addtime:<20}")

    print(f"\n共 {len(result)} 个域名")
    return 0


def cmd_add(args):
    """添加域名"""
    client = get_client(args.server)

    # 先获取站点信息获取站点 ID（不使用 search 参数，避免搜索问题）
    endpoint = "/datalist/data/get_data_list"
    params = {
        "table": "sites",
        "type": "-1",
        "p": 1,
        "limit": 100
    }

    result = client.request(endpoint, params)
    data = result.get('data', [])

    # 查找匹配的站点（支持 ID 或域名匹配）
    site_id = None
    for s in data:
        if str(s.get('id')) == str(args.name) or s.get('name') == args.name:
            site_id = s.get('id')
            break

    if not site_id:
        print(f"未找到站点：{args.name}")
        return 1

    endpoint = "/site?action=AddDomain"
    params = {
        "id": site_id,
        "domain": args.domain,
        "webname": args.name
    }

    result = client.request(endpoint, params)

    # 检查 API 返回结果
    if not result:
        print(f"❌ 域名添加失败：返回数据为空")
        return 1

    # 处理 API 错误响应
    if isinstance(result, dict):
        if result.get('status') is False:
            print(f"❌ 域名添加失败：{result.get('msg', '未知错误')}")
            return 1

    if result.get('domains'):
        print(f"\n✅ 域名添加结果:\n")
        for d in result['domains']:
            status = "✅" if d.get('status') else "❌"
            msg = d.get('msg', '')
            print(f"   {status} {d.get('name', '')}: {msg}")
        return 0
    else:
        print(f"❌ 域名添加失败：{result.get('msg', '未知错误')}")
        return 1


def cmd_delete(args):
    """删除域名"""
    client = get_client(args.server)

    # 先获取站点信息获取站点 ID（不使用 search 参数，避免搜索问题）
    endpoint = "/datalist/data/get_data_list"
    params = {
        "table": "sites",
        "type": "-1",
        "p": 1,
        "limit": 100
    }

    result = client.request(endpoint, params)
    data = result.get('data', [])

    # 查找匹配的站点（支持 ID 或域名匹配）
    site_id = None
    for s in data:
        if str(s.get('id')) == str(args.name) or s.get('name') == args.name:
            site_id = s.get('id')
            break

    if not site_id:
        print(f"未找到站点：{args.name}")
        return 1

    # 参数验证：必须提供 domain 或 domain_id 至少一个
    if not args.domain and not args.domain_id:
        print(f"❌ 删除域名失败：请指定要删除的域名 (-d) 或域名 ID (-i)")
        return 1

    # 如果没有指定 domain_id，但有域名，先查询域名 ID
    domain_ids = args.domain_id
    if not domain_ids and args.domain:
        print(f"⚠️  需要通过域名名称删除，先获取域名列表...")
        endpoint = "/data?action=getData"
        params = {
            "table": "domain",
            "list": "True",
            "search": site_id
        }
        domain_result = client.request(endpoint, params)

        # 查找匹配的域名 ID
        for d in domain_result if isinstance(domain_result, list) else []:
            if d.get('name') == args.domain:
                domain_ids = str(d.get('id'))
                print(f"   找到域名 ID: {domain_ids}")
                break

        if not domain_ids:
            print(f"❌ 未找到域名：{args.domain}")
            return 1

    endpoint = "/site?action=delete_domain_multiple"
    params = {
        "id": site_id,
        "domains_id": domain_ids
    }

    result = client.request(endpoint, params)

    if result.get('status'):
        print(f"\n✅ 域名删除结果:\n")
        if result.get('success'):
            for d in result['success']:
                print(f"   ✅ 已删除：{d}")
        if result.get('error'):
            for d, err in result['error'].items():
                print(f"   ❌ 失败：{d} - {err}")
        return 0
    else:
        print(f"❌ 域名删除失败：{result.get('msg', '未知错误')}")
        return 1


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='宝塔面板域名管理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '-s', '--server',
        help='服务器名称（使用 bt-config 配置的名称）'
    )

    subparsers = parser.add_subparsers(dest='command', help='命令')

    # list 命令
    list_parser = subparsers.add_parser('list', help='列出站点的所有域名')
    list_parser.add_argument('-n', '--name', required=True, help='站点域名')
    list_parser.set_defaults(func=cmd_list)

    # add 命令
    add_parser = subparsers.add_parser('add', help='添加域名')
    add_parser.add_argument('-n', '--name', required=True, help='站点域名')
    add_parser.add_argument('-d', '--domain', required=True, help='要添加的域名（多个用逗号分隔）')
    add_parser.set_defaults(func=cmd_add)

    # delete 命令
    delete_parser = subparsers.add_parser('delete', help='删除域名')
    delete_parser.add_argument('-n', '--name', required=True, help='站点域名')
    delete_parser.add_argument('-d', '--domain', help='要删除的域名')
    delete_parser.add_argument('-i', '--domain-id', help='域名 ID（多个用逗号分隔）')
    delete_parser.set_defaults(func=cmd_delete)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
