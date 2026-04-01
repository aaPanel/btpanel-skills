#!/usr/bin/env python3
# coding: utf-8
"""
SSL 证书管理 CLI 工具
提供 SSL 证书查询、上传、申请等功能
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
                    'timeout': server.timeout if hasattr(server, 'timeout') else server.get('timeout', 10000)
                }
                return BtClient(
                    name=config['name'],
                    host=config['host'],
                    token=config['token'],
                    timeout=config['timeout']
                )
        raise ValueError(f"未找到服务器：{server_name}")
    else:
        manager = BtClientManager()
        return manager.get_client()


def cmd_info(args):
    """获取 SSL 证书信息"""
    client = get_client(args.server)

    endpoint = "/site?action=GetSSL"
    params = {
        "siteName": args.name
    }

    try:
        result = client.request(endpoint, params)
    except RuntimeError as e:
        # API 返回错误，可能是未配置 SSL
        error_msg = str(e)
        if '不存在' in error_msg or '未配置' in error_msg or 'API请求失败' in error_msg:
            print(f"\n🔒 SSL 证书信息：{args.name}\n")
            print("   ❌ 未配置 SSL 证书")
            return 0
        raise

    if not result:
        print("获取 SSL 信息失败")
        return 1

    print(f"\n🔒 SSL 证书信息：{args.name}\n")

    # 检查是否配置 SSL（oid=-1 且没有 key 表示未配置）
    if result.get('oid') == -1 and not result.get('key'):
        print("   ❌ 未配置 SSL 证书")
        return 0

    # 基本信息
    print(f"强制 HTTPS: {'✅ 已开启' if result.get('httpTohttps') else '❌ 已关闭'}")
    print(f"HTTPS 模式：{'✅ 已开启' if result.get('https_mode') else '❌ 已关闭'}")

    # 证书信息
    cert_data = result.get('cert_data', {})
    if cert_data:
        print(f"\n📄 证书详情:")
        print(f"   颁发机构：{cert_data.get('issuer', 'Unknown')}")
        print(f"   证书主体：{cert_data.get('subject', 'Unknown')}")
        print(f"   有效期：{cert_data.get('notBefore', 'N/A')} ~ {cert_data.get('notAfter', 'N/A')}")

        endtime = cert_data.get('endtime', 0)
        if endtime < 0:
            print(f"   ⚠️  已过期 {abs(endtime)} 天")
        elif endtime < 30:
            print(f"   ⚠️  即将过期（剩余 {endtime} 天）")
        else:
            print(f"   剩余 {endtime} 天")

        dns = cert_data.get('dns', [])
        if dns:
            print(f"   绑定域名：{', '.join(dns)}")

    # TLS 版本
    tls = result.get('tls_versions', {})
    if tls:
        print(f"\n🔐 TLS 版本:")
        print(f"   TLSv1.0: {'✅' if tls.get('TLSv1') else '❌'}")
        print(f"   TLSv1.1: {'✅' if tls.get('TLSv1.1') else '❌'}")
        print(f"   TLSv1.2: {'✅' if tls.get('TLSv1.2') else '❌'}")
        print(f"   TLSv1.3: {'✅' if tls.get('TLSv1.3') else '❌'}")

    return 0


def cmd_upload(args):
    """上传 SSL 证书"""
    client = get_client(args.server)

    # 读取证书文件
    try:
        with open(args.cert, 'r', encoding='utf-8') as f:
            cert_content = f.read()
        with open(args.key, 'r', encoding='utf-8') as f:
            key_content = f.read()
    except Exception as e:
        print(f"❌ 读取证书文件失败：{e}")
        return 1

    endpoint = "/site?action=SetSSL"
    params = {
        "type": 1,
        "siteName": args.name,
        "key": key_content,
        "csr": cert_content
    }

    result = client.request(endpoint, params)

    if result.get('status'):
        print(f"✅ SSL 证书上传成功：{args.name}")
        return 0
    else:
        print(f"❌ SSL 证书上传失败：{result.get('msg', '未知错误')}")
        return 1


def cmd_apply(args):
    """申请免费 SSL 证书"""
    client = get_client(args.server)

    # 构造域名列表
    domains = args.domain.split(',') if ',' in args.domain else [args.domain]
    domains_json = '["' + '","'.join(domains) + '"]'

    endpoint = "/acme?action=apply_cert_api"
    params = {
        "domains": domains_json,
        "id": args.id,
        "auth_type": "http",
        "auth_to": domains_json,
        "auto_wildcard": 0,
        "ca": args.ca or "letsencrypt"
    }

    print(f"🔒 正在申请 SSL 证书...")
    print(f"   域名：{', '.join(domains)}")
    print(f"   CA 机构：{args.ca or 'Let\'s Encrypt'}")
    print(f"   验证方式：HTTP")

    result = client.request(endpoint, params)

    if result.get('status'):
        print(f"\n✅ SSL 证书申请成功")
        msg = result.get('msg', '')
        if msg:
            print(f"   {msg}")
        return 0
    else:
        print(f"\n⚠️  SSL 证书申请遇到问题")
        msg = result.get('msg', '')
        if msg:
            # msg 可能是数组
            if isinstance(msg, list):
                for m in msg:
                    print(f"   {m}")
            else:
                print(f"   {msg}")
        return 1


def cmd_https(args):
    """设置强制 HTTPS"""
    client = get_client(args.server)

    if args.enable:
        endpoint = "/site?action=HttpToHttps"
        action_msg = "已开启"
    elif args.disable:
        endpoint = "/site?action=CloseToHttps"
        action_msg = "已关闭"
    else:
        print("请指定 --enable 或 --disable")
        return 1

    params = {
        "siteName": args.name
    }

    result = client.request(endpoint, params)

    if result.get('status'):
        print(f"✅ 强制 HTTPS {action_msg}: {args.name}")
        return 0
    else:
        print(f"❌ 设置失败：{result.get('msg', '未知错误')}")
        return 1


def cmd_close(args):
    """关闭 SSL"""
    client = get_client(args.server)

    endpoint = "/site?action=CloseSSLConf"
    params = {
        "updateOf": 1,
        "siteName": args.name
    }

    result = client.request(endpoint, params)

    if result.get('status'):
        print(f"✅ SSL 已关闭：{args.name}")
        return 0
    else:
        print(f"❌ 关闭失败：{result.get('msg', '未知错误')}")
        return 1


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='宝塔面板 SSL 证书管理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '-s', '--server',
        help='服务器名称（使用 bt-config 配置的名称）'
    )

    subparsers = parser.add_subparsers(dest='command', help='命令')

    # info 命令
    info_parser = subparsers.add_parser('info', help='查看 SSL 证书信息')
    info_parser.add_argument('-n', '--name', required=True, help='站点域名')
    info_parser.set_defaults(func=cmd_info)

    # upload 命令
    upload_parser = subparsers.add_parser('upload', help='上传 SSL 证书')
    upload_parser.add_argument('-n', '--name', required=True, help='站点域名')
    upload_parser.add_argument('--key', required=True, help='私钥文件路径')
    upload_parser.add_argument('--cert', required=True, help='证书文件路径')
    upload_parser.set_defaults(func=cmd_upload)

    # apply 命令
    apply_parser = subparsers.add_parser('apply', help='申请免费 SSL 证书')
    apply_parser.add_argument('-n', '--name', required=True, help='站点域名')
    apply_parser.add_argument('-d', '--domain', required=True, help='域名（多个用逗号分隔）')
    apply_parser.add_argument('--id', type=int, help='站点 ID')
    apply_parser.add_argument('--ca', choices=['letsencrypt', 'litessl'], help='CA 机构')
    apply_parser.set_defaults(func=cmd_apply)

    # https 命令
    https_parser = subparsers.add_parser('https', help='设置强制 HTTPS')
    https_parser.add_argument('-n', '--name', required=True, help='站点域名')
    https_group = https_parser.add_mutually_exclusive_group(required=True)
    https_group.add_argument('--enable', action='store_true', help='开启强制 HTTPS')
    https_group.add_argument('--disable', action='store_true', help='关闭强制 HTTPS')
    https_parser.set_defaults(func=cmd_https)

    # close 命令
    close_parser = subparsers.add_parser('close', help='关闭 SSL')
    close_parser.add_argument('-n', '--name', required=True, help='站点域名')
    close_parser.set_defaults(func=cmd_close)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
