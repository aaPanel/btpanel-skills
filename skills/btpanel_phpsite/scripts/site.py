#!/usr/bin/env python3
# coding: utf-8
"""
PHP 站点管理 CLI 工具
提供站点创建、删除、启停、查询等功能
"""

import argparse
import json
import sys
from pathlib import Path

# 兼容开发环境和发布环境的导入
_skill_root = Path(__file__).parent.parent
if (_skill_root / "bt_common").exists():
    # 发布环境：脚本在 {baseDir}/scripts/, bt_common 在 {baseDir}/bt_common/
    sys.path.insert(0, str(_skill_root))
else:
    # 开发环境：脚本在 src/btpanel_phpsite/scripts/, bt_common 在 src/bt_common/
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


def get_site_id(client, site_name: str) -> int:
    """根据站点名称或 ID 获取站点 ID"""
    # 如果传入的是数字，直接返回
    if site_name.isdigit():
        return int(site_name)
    
    # 获取站点列表查找
    endpoint = "/datalist/data/get_data_list"
    params = {
        "table": "sites",
        "type": "-1",
        "p": 1,
        "limit": 100
    }
    
    result = client.request(endpoint, params)
    data = result.get('data', [])
    
    for s in data:
        if s.get('name') == site_name:
            return s.get('id')
    
    return None


def cmd_list(args):
    """列出所有站点"""
    client = get_client(args.server)

    # 调用 API 获取站点列表
    endpoint = "/datalist/data/get_data_list"
    params = {
        "table": "sites",
        "type": "-1",
        "p": 1,
        "limit": 100
    }

    result = client.request(endpoint, params)

    if not result:
        print("获取站点列表失败")
        return 1

    data = result.get('data', [])

    if not data:
        print("暂无站点")
        return 0

    print("\n📊 站点列表\n")
    print(f"{'ID':<6} {'域名':<30} {'状态':<8} {'PHP 版本':<10} {'路径':<40} {'备注':<20}")
    print("-" * 120)

    for site in data:
        site_id = site.get('id', 0)
        name = site.get('name', 'unknown')
        status = "✅ 启用" if site.get('status') == '1' else "❌ 停用"
        php_version = site.get('php_version', '静态')
        path = site.get('path', '')[:38]
        ps = site.get('ps', '')[:18]

        print(f"{site_id:<6} {name:<30} {status:<8} {php_version:<10} {path:<40} {ps:<20}")

    print(f"\n共 {len(data)} 个站点")
    return 0


def cmd_add(args):
    """创建新站点"""
    client = get_client(args.server)

    # 构造 webname JSON
    port = 80
    args.name = args.name.strip()
    try:
        if ":" in args.name:
            if args.name.startswith("[") and "]" in args.name:
                if args.name[-1] != "]":
                    port = args.name.rsplit(':', 1)[1]
            else:
                port = args.name.rsplit(':', 1)[1]
    except:
        import traceback
        traceback.print_exc()
        print("无效的站点名称:", args.name)
        return 1

    webname = json.dumps({
        "domain": args.name,
        "domainlist": [],
        "count": 0
    }, ensure_ascii=False)

    # 构造请求参数
    # 注意：sql 和 ftp 参数必须明确传递 "true" 或 "false"
    # 宝塔 API 要求明确指定是否需要创建数据库和 FTP
    params = {
        "webname": webname,
        "path": args.path or f"/www/wwwroot/{args.name.replace(':', '_')}",
        "type": "php",
        "version": args.version,
        "port": port,
        "ps": args.ps or "",
        "sql": "false",  # 默认不创建数据库
        "ftp": "false"   # 默认不创建 FTP
    }

    # 如果创建数据库
    if args.create_db:
        params["sql"] = "true"
        params["codeing"] = args.db_encoding or "utf8"
        params["datauser"] = args.db_user or args.name.replace('.', '_')
        params["datapassword"] = args.db_password or _generate_password()

    # 如果创建 FTP
    if args.create_ftp:
        params["ftp"] = "true"
        params["ftp_username"] = args.ftp_user or args.name.replace('.', '_')
        params["ftp_password"] = args.ftp_password or _generate_password()

    endpoint = "/site?action=AddSite"
    result = client.request(endpoint, params)

    if result.get('siteStatus') or result.get('status'):
        print(f"✅ 站点创建成功：{args.name}")
        print(f"   路径：{params['path']}")
        print(f"   PHP 版本：{args.version}")
        print(f"   站点 ID: {result.get('siteId', 'N/A')}")

        if args.create_db and result.get('databaseStatus'):
            print(f"   ✅ 数据库创建成功")
            print(f"      数据库名：{result.get('databaseName', 'N/A')}")
            print(f"      用户名：{result.get('databaseUser', 'N/A')}")
            print(f"      密码：{result.get('databasePass', 'N/A')}")
        elif args.create_db:
            print(f"   ⚠️  数据库创建失败：{result.get('msg', '未知错误')}")

        if args.create_ftp and result.get('ftpStatus'):
            print(f"   ✅ FTP 创建成功")
            print(f"      用户名：{result.get('ftpUser', 'N/A')}")
            print(f"      密码：{result.get('ftpPass', 'N/A')}")
        elif args.create_ftp:
            print(f"   ⚠️  FTP 创建失败：{result.get('msg', '未知错误')}")

        if result.get('siteId'):
            print(f"   站点 ID: {result.get('siteId')}")

        return 0
    else:
        print(f"❌ 站点创建失败：{result.get('msg', '未知错误')}")
        return 1


def cmd_stop(args):
    """停用站点"""
    client = get_client(args.server)

    # 获取站点 ID
    site_id = args.id or get_site_id(client, args.name)
    if not site_id:
        print(f"❌ 未找到站点：{args.name}")
        return 1

    endpoint = "/site?action=SiteStop"
    params = {
        "id": site_id,
        "name": args.name
    }

    result = client.request(endpoint, params)

    if result.get('status'):
        print(f"✅ 站点已停用：{args.name}")
        return 0
    else:
        print(f"❌ 停用失败：{result.get('msg', '未知错误')}")
        return 1


def cmd_start(args):
    """启用站点"""
    client = get_client(args.server)

    # 获取站点 ID
    site_id = args.id or get_site_id(client, args.name)
    if not site_id:
        print(f"❌ 未找到站点：{args.name}")
        return 1

    endpoint = "/site?action=SiteStart"
    params = {
        "id": site_id,
        "name": args.name
    }

    result = client.request(endpoint, params)

    if result.get('status'):
        print(f"✅ 站点已启用：{args.name}")
        return 0
    else:
        print(f"❌ 启用失败：{result.get('msg', '未知错误')}")
        return 1


def cmd_delete(args):
    """删除站点"""
    client = get_client(args.server)

    # 获取站点 ID（如果未提供）
    site_id = args.id
    if not site_id:
        site_id = get_site_id(client, args.name)
        if not site_id:
            print(f"❌ 未找到站点：{args.name}")
            return 1

    endpoint = "/site?action=DeleteSite"
    params = {
        "id": site_id,
        "webname": args.name,
        "ftp": 1 if args.delete_ftp else 0,
        "database": 1 if args.delete_db else 0,
        "path": 1 if args.delete_path else 0
    }

    try:
        result = client.request(endpoint, params)
        
        # API 返回 status=true 表示成功
        if result.get('status'):
            print(f"✅ 站点已删除：{args.name}")
            if args.delete_path:
                print("   ⚠️  站点目录已删除")
            if args.delete_db:
                print("   ⚠️  关联数据库已删除")
            if args.delete_ftp:
                print("   ⚠️  关联 FTP 已删除")
            return 0
        else:
            print(f"❌ 删除失败：{result.get('msg', '未知错误')}")
            return 1
    except RuntimeError as e:
        # API 可能返回错误但实际删除成功，需要验证
        error_msg = str(e)
        if '不存在' in error_msg:
            # 站点可能已被删除，验证一下
            verify_id = get_site_id(client, args.name)
            if not verify_id:
                print(f"✅ 站点已删除：{args.name}（API 返回错误但实际成功）")
                if args.delete_path:
                    print("   ⚠️  站点目录已删除")
                if args.delete_db:
                    print("   ⚠️  关联数据库已删除")
                if args.delete_ftp:
                    print("   ⚠️  关联 FTP 已删除")
                return 0
        print(f"❌ 删除失败：{error_msg}")
        return 1


def cmd_info(args):
    """查看站点详情"""
    client = get_client(args.server)

    # 先获取站点列表找到站点（不使用 search 参数，避免搜索问题）
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
    site = None
    for s in data:
        if str(s.get('id')) == str(args.name) or s.get('name') == args.name:
            site = s
            break

    if not site:
        print(f"未找到站点：{args.name}")
        return 1

    print(f"\n📊 站点详情：{args.name}\n")
    print(f"ID: {site.get('id')}")
    print(f"域名：{site.get('name')}")
    print(f"状态：{'✅ 启用' if site.get('status') == '1' else '❌ 停用'}")
    print(f"路径：{site.get('path')}")
    print(f"PHP 版本：{site.get('php_version', '静态')}")
    print(f"备注：{site.get('ps', '无')}")
    print(f"创建时间：{site.get('addtime')}")
    print(f"绑定域名数：{site.get('domain', 0)}")
    print(f"备份数量：{site.get('backup_count', 0)}")

    # SSL 信息
    ssl = site.get('ssl')
    if ssl and ssl != -1:
        print(f"\n🔒 SSL 证书:")
        print(f"   颁发机构：{ssl.get('issuer', 'Unknown')}")
        print(f"   有效期：{ssl.get('notBefore', 'N/A')} ~ {ssl.get('notAfter', 'N/A')}")
        endtime = ssl.get('endtime', 0)
        if endtime < 0:
            print(f"   ⚠️  已过期 {abs(endtime)} 天")
        elif endtime < 30:
            print(f"   ⚠️  即将过期（剩余 {endtime} 天）")
        else:
            print(f"   剩余 {endtime} 天")

    return 0


def cmd_set_path(args):
    """修改站点路径"""
    client = get_client(args.server)

    # 获取站点 ID
    site_id = args.id or get_site_id(client, args.name)
    if not site_id:
        print(f"❌ 未找到站点：{args.name}")
        return 1

    endpoint = "/site?action=SetPath"
    params = {
        "id": site_id,
        "path": args.path
    }

    result = client.request(endpoint, params)

    if result.get('status'):
        print(f"✅ 站点路径已修改：{args.name}")
        print(f"   新路径：{args.path}")
        return 0
    else:
        print(f"❌ 修改失败：{result.get('msg', '未知错误')}")
        return 1


def _generate_password(length=16):
    """生成随机密码"""
    import random
    import string
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='宝塔面板 PHP 站点管理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '-s', '--server',
        help='服务器名称（使用 bt-config 配置的名称）'
    )

    subparsers = parser.add_subparsers(dest='command', help='命令')

    # list 命令
    list_parser = subparsers.add_parser('list', help='列出所有站点')
    list_parser.set_defaults(func=cmd_list)

    # add 命令
    add_parser = subparsers.add_parser('add', help='创建新站点')
    add_parser.add_argument('-n', '--name', required=True, help='站点域名')
    add_parser.add_argument('-p', '--path', help='站点路径')
    add_parser.add_argument('-v', '--version', default='82', help='PHP 版本（如 82, 81, 74 等）')
    add_parser.add_argument('--ps', help='备注说明')
    add_parser.add_argument('--create-db', action='store_true', help='创建数据库')
    add_parser.add_argument('--db-user', help='数据库用户名')
    add_parser.add_argument('--db-password', help='数据库密码')
    add_parser.add_argument('--db-encoding', default='utf8', help='数据库编码')
    add_parser.add_argument('--create-ftp', action='store_true', help='创建 FTP')
    add_parser.add_argument('--ftp-user', help='FTP 用户名')
    add_parser.add_argument('--ftp-password', help='FTP 密码')
    add_parser.set_defaults(func=cmd_add)

    # stop 命令
    stop_parser = subparsers.add_parser('stop', help='停用站点')
    stop_parser.add_argument('-n', '--name', required=True, help='站点域名')
    stop_parser.add_argument('-i', '--id', type=int, help='站点 ID')
    stop_parser.set_defaults(func=cmd_stop)

    # start 命令
    start_parser = subparsers.add_parser('start', help='启用站点')
    start_parser.add_argument('-n', '--name', required=True, help='站点域名')
    start_parser.add_argument('-i', '--id', type=int, help='站点 ID')
    start_parser.set_defaults(func=cmd_start)

    # delete 命令
    delete_parser = subparsers.add_parser('delete', help='删除站点')
    delete_parser.add_argument('-n', '--name', required=True, help='站点域名')
    delete_parser.add_argument('-i', '--id', type=int, help='站点 ID')
    delete_parser.add_argument('--delete-path', action='store_true', help='删除站点目录')
    delete_parser.add_argument('--delete-db', action='store_true', help='删除关联数据库')
    delete_parser.add_argument('--delete-ftp', action='store_true', help='删除关联 FTP')
    delete_parser.set_defaults(func=cmd_delete)

    # info 命令
    info_parser = subparsers.add_parser('info', help='查看站点详情')
    info_parser.add_argument('-n', '--name', required=True, help='站点域名')
    info_parser.set_defaults(func=cmd_info)

    # set-path 命令
    set_path_parser = subparsers.add_parser('set-path', help='修改站点路径')
    set_path_parser.add_argument('-n', '--name', required=True, help='站点域名')
    set_path_parser.add_argument('-p', '--path', required=True, help='新的站点路径')
    set_path_parser.add_argument('-i', '--id', type=int, help='站点 ID')
    set_path_parser.set_defaults(func=cmd_set_path)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
