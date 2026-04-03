#!/usr/bin/env python3
# coding: utf-8
"""
数据库管理 CLI 工具
提供 MySQL 数据库创建、删除、查询、优化等功能
"""

import argparse
import json
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


def _generate_password(length=16):
    """生成随机密码"""
    import random
    import string
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def cmd_list(args):
    """列出所有数据库"""
    client = get_client(args.server)

    endpoint = "/datalist/data/get_data_list"
    params = {
        "table": "databases",
        "p": 1,
        "limit": 100
    }

    result = client.request(endpoint, params)

    if not result:
        print("获取数据库列表失败")
        return 1

    data = result.get('data', [])

    if not data:
        print("暂无数据库")
        return 0

    print("\n📊 数据库列表\n")
    print(f"{'ID':<6} {'数据库名':<25} {'用户名':<25} {'权限':<15} {'大小':<12} {'创建时间':<20}")
    print("-" * 110)

    for db in data:
        db_id = db.get('id', 0)
        name = db.get('name', 'unknown')
        username = db.get('username', 'unknown')
        accept = db.get('accept', '127.0.0.1')
        quota = db.get('quota', {})
        size = quota.get('used', 0)
        size_str = format_size(size)
        addtime = db.get('addtime', 'unknown')

        print(f"{db_id:<6} {name:<25} {username:<25} {accept:<15} {size_str:<12} {addtime:<20}")

    print(f"\n共 {len(data)} 个数据库")
    return 0


def cmd_add(args):
    """创建数据库（已移除）
    
    注意：独立的数据库创建功能已移除。
    如需创建数据库，请在创建站点时使用 --create-db 参数。
    
    示例:
        python3 site.py add -n example.com --create-db -d example_db -u example_user -P "password"
    """
    print("⚠️  独立的数据库创建功能已移除")
    print()
    print("💡 建议：在创建站点时同时创建数据库")
    print("   示例:")
    print("   python3 site.py add -n example.com --create-db -d example_db -u example_user -P \"password\"")
    return 1


# def cmd_add(args):
#     """创建数据库"""
#     client = get_client(args.server)
# 
#     # 根据 API 文档，参数应该是 username 而不是 datauser
#     endpoint = "/database?action=addDatabase"
#     params = {
#         "name": args.name,
#         "username": args.user or args.name.replace('-', '_').replace('.', '_'),
#         "password": args.password or _generate_password(),
#         "accept": args.access or "127.0.0.1",
#         "codeing": args.encoding or "utf8",
#         "ps": args.ps or ""
#     }
# 
#     result = client.request(endpoint, params)
# 
#     if result.get('status'):
#         print(f"✅ 数据库创建成功：{args.name}")
#         print(f"   用户名：{params['username']}")
#         print(f"   密码：{params['password']}")
#         print(f"   访问权限：{params['accept']}")
#         print(f"   编码：{params['codeing']}")
#         if result.get('id'):
#             print(f"   数据库 ID: {result.get('id')}")
#         return 0
#     else:
#         print(f"❌ 数据库创建失败：{result.get('msg', '未知错误')}")
#         return 1


def cmd_info(args):
    """查看数据库详情"""
    client = get_client(args.server)

    # 获取数据库列表找到数据库
    endpoint = "/datalist/data/get_data_list"
    params = {
        "table": "databases",
        "search": args.database,
        "p": 1,
        "limit": 10
    }

    result = client.request(endpoint, params)
    data = result.get('data', [])

    # 查找匹配的数据库
    db = None
    for d in data:
        if d.get('name') == args.database:
            db = d
            break

    if not db:
        print(f"未找到数据库：{args.database}")
        return 1

    print(f"\n📊 数据库详情：{args.database}\n")
    print(f"ID: {db.get('id')}")
    print(f"数据库名：{db.get('name')}")
    print(f"用户名：{db.get('username')}")
    print(f"密码：{db.get('password')}")
    print(f"访问权限：{db.get('accept')}")
    print(f"备注：{db.get('ps', '无')}")
    print(f"创建时间：{db.get('addtime')}")

    # 配额信息
    quota = db.get('quota', {})
    if quota:
        used = quota.get('used', 0)
        size = quota.get('size', 0)
        print(f"\n💾 存储信息:")
        print(f"   已使用：{format_size(used)}")
        if size > 0:
            print(f"   配额：{format_size(size)}")
        else:
            print(f"   配额：无限制")

    return 0


def cmd_password(args):
    """修改数据库密码"""
    client = get_client(args.server)

    # 先获取数据库信息
    endpoint = "/datalist/data/get_data_list"
    params = {
        "table": "databases",
        "search": args.database,
        "p": 1,
        "limit": 10
    }

    result = client.request(endpoint, params)
    data = result.get('data', [])

    # 查找匹配的数据库
    db = None
    for d in data:
        if d.get('name') == args.database:
            db = d
            break

    if not db:
        print(f"未找到数据库：{args.database}")
        return 1

    endpoint = "/database?action=ResDatabasePassword"
    params = {
        "id": db.get('id'),
        "name": db.get('username'),
        "password": args.password,
        "data_name": args.database
    }

    result = client.request(endpoint, params)

    if result.get('status'):
        print(f"✅ 数据库密码已修改：{args.database}")
        print(f"   新密码：{args.password}")
        return 0
    else:
        print(f"❌ 密码修改失败：{result.get('msg', '未知错误')}")
        return 1


def cmd_access(args):
    """设置数据库访问权限"""
    client = get_client(args.server)

    endpoint = "/database?action=SetDatabaseAccess"
    params = {
        "name": args.database,
        "access": args.access,
        "dataAccess": "1"
    }

    # 如果是指定 IP，需要设置 address
    if args.access not in ['127.0.0.1', '%', 'localhost']:
        params["address"] = args.access

    result = client.request(endpoint, params)

    if result.get('status'):
        print(f"✅ 数据库访问权限已设置：{args.database}")
        print(f"   新权限：{args.access}")
        return 0
    else:
        print(f"❌ 权限设置失败：{result.get('msg', '未知错误')}")
        return 1


def cmd_tables(args):
    """查看数据库表信息"""
    client = get_client(args.server)

    endpoint = "/database?action=GetInfo"
    params = {
        "db_name": args.database
    }

    result = client.request(endpoint, params)

    if not result:
        print("获取数据库表信息失败")
        return 1

    print(f"\n📊 数据库表信息：{args.database}\n")
    print(f"数据库大小：{result.get('data_size', 'unknown')}")
    print(f"\n{'表名':<40} {'引擎':<12} {'行数':<10} {'大小':<12} {'注释':<20}")
    print("-" * 100)

    tables = result.get('tables', [])
    for table in tables:
        table_name = table.get('table_name', 'unknown')
        table_type = table.get('type', 'unknown')
        rows = table.get('rows_count', 0)
        size = table.get('data_size', 'unknown')
        comment = table.get('comment', '')

        print(f"{table_name:<40} {table_type:<12} {rows:<10} {size:<12} {comment:<20}")

    print(f"\n共 {len(tables)} 个表")
    return 0


def cmd_optimize(args):
    """优化数据库表"""
    client = get_client(args.server)

    # 先获取表列表
    endpoint = "/database?action=GetInfo"
    params = {
        "db_name": args.database
    }

    result = client.request(endpoint, params)
    tables = result.get('tables', [])

    if not tables:
        print("未找到任何表")
        return 1

    table_names = json.dumps([t.get('table_name') for t in tables], ensure_ascii=False)

    endpoint = "/database?action=OpTable"
    params = {
        "db_name": args.database,
        "tables": table_names
    }

    result = client.request(endpoint, params)

    if result.get('status'):
        print(f"✅ 数据库表优化完成：{args.database}")
        print(f"   优化表数：{len(tables)}")
        return 0
    else:
        print(f"❌ 优化失败：{result.get('msg', '未知错误')}")
        return 1


def cmd_repair(args):
    """修复数据库表"""
    client = get_client(args.server)

    # 先获取表列表
    endpoint = "/database?action=GetInfo"
    params = {
        "db_name": args.database
    }

    result = client.request(endpoint, params)
    tables = result.get('tables', [])

    if not tables:
        print("未找到任何表")
        return 1

    table_names = json.dumps([t.get('table_name') for t in tables], ensure_ascii=False)

    endpoint = "/database?action=ReTable"
    params = {
        "db_name": args.database,
        "tables": table_names
    }

    result = client.request(endpoint, params)

    if result.get('status'):
        print(f"✅ 数据库表修复完成：{args.database}")
        print(f"   修复表数：{len(tables)}")
        return 0
    else:
        print(f"❌ 修复失败：{result.get('msg', '未知错误')}")
        return 1


def cmd_delete(args):
    """删除数据库"""
    client = get_client(args.server)

    # 先获取数据库信息
    endpoint = "/datalist/data/get_data_list"
    params = {
        "table": "databases",
        "search": args.database,
        "p": 1,
        "limit": 10
    }

    result = client.request(endpoint, params)
    data = result.get('data', [])

    # 查找匹配的数据库
    db = None
    for d in data:
        if d.get('name') == args.database:
            db = d
            break

    if not db:
        print(f"未找到数据库：{args.database}")
        return 1

    endpoint = "/database?action=delDatabase"
    params = {
        "id": db.get('id'),
        "name": args.database
    }

    result = client.request(endpoint, params)

    if result.get('status'):
        print(f"✅ 数据库已删除：{args.database}")
        return 0
    else:
        print(f"❌ 删除失败：{result.get('msg', '未知错误')}")
        return 1


def format_size(size_bytes: int) -> str:
    """格式化大小"""
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f}KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / 1024 / 1024:.2f}MB"
    else:
        return f"{size_bytes / 1024 / 1024 / 1024:.2f}GB"


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='宝塔面板数据库管理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '-s', '--server',
        help='服务器名称（使用 bt-config 配置的名称）'
    )

    subparsers = parser.add_subparsers(dest='command', help='命令')

    # list 命令
    list_parser = subparsers.add_parser('list', help='列出所有数据库')
    list_parser.set_defaults(func=cmd_list)

    # add 命令（已禁用，保留帮助提示）
    add_parser = subparsers.add_parser('add', help='创建数据库（已禁用，请在创建站点时创建）')
    add_parser.set_defaults(func=cmd_add)

    # info 命令
    info_parser = subparsers.add_parser('info', help='查看数据库详情')
    info_parser.add_argument('-d', '--database', required=True, help='数据库名称')
    info_parser.set_defaults(func=cmd_info)

    # password 命令
    password_parser = subparsers.add_parser('password', help='修改数据库密码')
    password_parser.add_argument('-d', '--database', required=True, help='数据库名称')
    password_parser.add_argument('-P', '--password', required=True, help='新密码')
    password_parser.set_defaults(func=cmd_password)

    # access 命令
    access_parser = subparsers.add_parser('access', help='设置数据库访问权限')
    access_parser.add_argument('-d', '--database', required=True, help='数据库名称')
    access_parser.add_argument('-a', '--access', required=True, help='访问权限（127.0.0.1/%/IP）')
    access_parser.set_defaults(func=cmd_access)

    # tables 命令
    tables_parser = subparsers.add_parser('tables', help='查看数据库表信息')
    tables_parser.add_argument('-d', '--database', required=True, help='数据库名称')
    tables_parser.set_defaults(func=cmd_tables)

    # optimize 命令
    optimize_parser = subparsers.add_parser('optimize', help='优化数据库表')
    optimize_parser.add_argument('-d', '--database', required=True, help='数据库名称')
    optimize_parser.set_defaults(func=cmd_optimize)

    # repair 命令
    repair_parser = subparsers.add_parser('repair', help='修复数据库表')
    repair_parser.add_argument('-d', '--database', required=True, help='数据库名称')
    repair_parser.set_defaults(func=cmd_repair)

    # delete 命令
    delete_parser = subparsers.add_parser('delete', help='删除数据库')
    delete_parser.add_argument('-d', '--database', required=True, help='数据库名称')
    delete_parser.set_defaults(func=cmd_delete)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
