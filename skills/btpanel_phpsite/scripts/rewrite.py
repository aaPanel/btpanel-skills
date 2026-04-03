#!/usr/bin/env python3
# coding: utf-8
"""
伪静态规则管理 CLI 工具
提供伪静态规则查询、应用等功能
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
        return manager.get_client(server_name)


def cmd_list(args):
    """获取伪静态模板列表"""
    client = get_client(args.server)

    endpoint = "/site?action=GetRewriteList"
    params = {
        "siteName": args.name
    }

    result = client.request(endpoint, params)

    if not result:
        print("获取伪静态模板列表失败")
        return 1

    rewrite_list = result.get('rewrite', [])
    default_list = result.get('default_list', [])

    print(f"\n📋 伪静态模板列表：{args.name}\n")

    # 显示模板
    templates = []
    for t in rewrite_list:
        if t == "0.当前":
            templates.append(("📍 当前", t))
        elif t.lower() in ['wordpress', 'thinkphp', 'laravel5', 'dedecms', 'discuz', 'typecho', 'zblog', 'drupal', 'ecshop', 'phpcms', 'maccms', 'crmeb', 'shopwind', 'empirecms', 'edusoho', 'emlog', 'pbootcms']:
            templates.append(("✅ 推荐", t))
        else:
            templates.append(("   ", t))

    # 排序：当前 > 推荐 > 其他
    current = [t for t in templates if t[0] == "📍 当前"]
    recommended = [t for t in templates if t[0] == "✅ 推荐"]
    others = [t for t in templates if t[0] == "   "]

    if current:
        print("当前使用:")
        for icon, t in current:
            print(f"   {t}")
        print()

    if recommended:
        print("推荐模板:")
        for icon, t in recommended:
            print(f"   {icon} {t}")
        print()

    if others:
        print("其他模板:")
        for icon, t in others[:20]:  # 限制显示数量
            print(f"   {t}")
        if len(others) > 20:
            print(f"   ... 还有 {len(others) - 20} 个模板")

    return 0


def cmd_get(args):
    """获取当前伪静态规则"""
    client = get_client(args.server)

    # 获取站点伪静态文件路径
    path = f"/www/server/panel/vhost/rewrite/{args.name}.conf"

    endpoint = "/files?action=GetFileBody"
    params = {
        "path": path
    }

    result = client.request(endpoint, params)

    # 检查 API 返回
    if not result:
        print("获取伪静态规则失败：返回数据为空")
        return 1

    if isinstance(result, dict) and result.get('status') is False:
        print(f"获取伪静态规则失败：{result.get('msg', '未知错误')}")
        return 1

    data = result.get('data', '')

    print(f"\n📋 站点伪静态规则：{args.name}\n")
    print("-" * 50)
    print(data)
    print("-" * 50)

    return 0


def cmd_set(args):
    """设置伪静态规则"""
    client = get_client(args.server)

    if args.template:
        # 应用模板
        # 先获取面板配置，确定 Web 服务器类型（nginx/apache）
        config_endpoint = "/panel/public/get_public_config"
        config_result = client.request(config_endpoint)
        
        webserver = config_result.get('webserver', 'nginx').lower()
        
        # 根据 Web 服务器类型构建模板路径
        template_path = f"/www/server/panel/rewrite/{webserver}/{args.template}.conf"

        endpoint = "/files?action=GetFileBody"
        params = {
            "path": template_path
        }

        template_result = client.request(endpoint, params)

        if not template_result.get('status'):
            print(f"获取模板内容失败：{template_result.get('msg', '未知错误')}")
            print(f"模板路径：{template_path}")
            return 1

        content = template_result.get('data', '')
    elif args.custom:
        # 使用自定义规则
        content = args.custom
    else:
        print("请指定模板名称 (--template) 或自定义规则 (--custom)")
        return 1

    # 保存到站点伪静态文件
    path = f"/www/server/panel/vhost/rewrite/{args.name}.conf"

    endpoint = "/files?action=SaveFileBody"
    params = {
        "path": path,
        "data": content,
        "encoding": "utf-8"
    }

    result = client.request(endpoint, params)

    if result.get('status'):
        if args.template:
            print(f"✅ 已应用伪静态模板：{args.template}")
        else:
            print(f"✅ 已保存自定义伪静态规则")
        return 0
    else:
        print(f"❌ 保存失败：{result.get('msg', '未知错误')}")
        return 1


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='宝塔面板伪静态规则管理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '-s', '--server',
        help='服务器名称（使用 bt-config 配置的名称）'
    )

    subparsers = parser.add_subparsers(dest='command', help='命令')

    # list 命令
    list_parser = subparsers.add_parser('list', help='获取伪静态模板列表')
    list_parser.add_argument('-n', '--name', required=True, help='站点域名')
    list_parser.set_defaults(func=cmd_list)

    # get 命令
    get_parser = subparsers.add_parser('get', help='获取当前伪静态规则')
    get_parser.add_argument('-n', '--name', required=True, help='站点域名')
    get_parser.set_defaults(func=cmd_get)

    # set 命令
    set_parser = subparsers.add_parser('set', help='设置伪静态规则')
    set_parser.add_argument('-n', '--name', required=True, help='站点域名')
    set_parser.add_argument('-t', '--template', help='伪静态模板名称')
    set_parser.add_argument('--custom', help='自定义伪静态规则内容')
    set_parser.set_defaults(func=cmd_set)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
