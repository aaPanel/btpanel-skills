#!/usr/bin/env python3
# coding: utf-8
"""
SSL 证书管理 CLI 工具
提供 SSL 证书查询、上传、申请、部署等功能
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

    # 步骤 1: 获取站点 ID（如果未提供）
    site_id = args.id
    if not site_id:
        # 使用 GetSiteDomains 获取站点信息（包含 ID）
        endpoint = "/site?action=GetSiteDomains"
        params = {"siteName": args.name}
        try:
            domains_result = client.request(endpoint, params)
            if domains_result and isinstance(domains_result, dict):
                site_id = str(domains_result.get('id', ''))
        except Exception:
            pass
        
        # 如果还是没找到，尝试从站点列表获取
        if not site_id:
            endpoint = "/site?action=GetSiteList"
            try:
                sites_result = client.request(endpoint, {})
                sites = sites_result.get('data', [])
                for site in sites:
                    if site.get('name') == args.name:
                        site_id = str(site.get('id'))
                        break
            except Exception:
                pass
        
        if not site_id:
            print(f"❌ 未找到站点：{args.name}")
            print(f"\n💡 请使用 --id 参数指定站点 ID")
            return 1
        
        print(f"📊 站点 ID: {site_id}")

    # 构造域名列表
    domains = args.domain.split(',') if ',' in args.domain else [args.domain]
    
    # 检查是否包含 IP 地址
    import re
    ip_pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
    ip_domains = [d for d in domains if ip_pattern.match(d)]
    
    if ip_domains:
        print("❌ 无法为 IP 地址申请 SSL 证书")
        print(f"   无效的域名：{', '.join(ip_domains)}")
        print("\n⚠️  Let's Encrypt 仅支持域名申请证书，不支持 IP 地址")
        print("\n💡 解决方案：")
        print("   1. 使用域名代替 IP 地址")
        print("   2. 确保域名已解析到当前服务器")
        print("   3. 如果是通配符证书或在宝塔购买了域名，可使用 DNS 验证方式")
        return 1
    
    domains_json = '["' + '","'.join(domains) + '"]'

    # 步骤 2: 申请证书
    endpoint = "/acme?action=apply_cert_api"
    params = {
        "domains": domains_json,
        "id": site_id,
        "auth_type": args.auth_type or "http",
        "auth_to": domains_json,
        "auto_wildcard": 1 if args.wildcard else 0,
        "ca": args.ca or "letsencrypt"
    }

    print(f"\n🔒 正在申请 SSL 证书...")
    print(f"   站点：{args.name} (ID: {site_id})")
    print(f"   域名：{', '.join(domains)}")
    print(f"   CA 机构：{args.ca or 'Let\'s Encrypt'}")
    print(f"   验证方式：{args.auth_type or 'HTTP'}")
    if args.wildcard:
        print(f"   通配符：✅ 启用")

    result = client.request(endpoint, params)

    if result.get('status'):
        print(f"\n✅ SSL 证书申请成功")
        msg = result.get('msg', '')
        if msg:
            print(f"   {msg}")
        print(f"\n💡 提示：")
        print(f"   证书申请成功后会自动应用到站点")
        print(f"   可在订单列表查看进度：python3 ssl_cert.py orders -n {args.name}")
        return 0
    else:
        print(f"\n❌ SSL 证书申请失败")
        msg = result.get('msg', '')
        if msg:
            # msg 可能是数组
            if isinstance(msg, list):
                for m in msg:
                    print(f"   {m}")
            else:
                print(f"   {msg}")
        
        # 查看日志获取详细错误信息
        print(f"\n🔍 正在查看申请日志...")
        log_path = "/www/server/panel/logs/letsencrypt.log"
        
        try:
            # 读取日志文件最后 50 行
            log_endpoint = "/files?action=GetFileBody"
            log_params = {"path": log_path}
            log_result = client.request(log_endpoint, log_params)
            
            if log_result and isinstance(log_result, dict) and log_result.get('data'):
                log_content = log_result.get('data', '')
                log_lines = log_content.split('\n')[-50:]  # 最后 50 行
                
                # 过滤出错误相关日志
                error_lines = []
                for line in log_lines:
                    if any(keyword in line.lower() for keyword in ['error', 'fail', 'invalid', 'timeout', 'denied']):
                        error_lines.append(line)
                
                if error_lines:
                    print(f"\n📄 日志中的错误信息:")
                    for line in error_lines[-10:]:  # 显示最近 10 条错误
                        print(f"   {line}")
                
                print(f"\n💡 解决方案:")
                print(f"   1. 检查域名是否已解析到当前服务器")
                print(f"   2. 检查 80 端口是否开放（HTTP 验证）")
                print(f"   3. 检查 DNS API 配置是否正确（DNS 验证）")
                print(f"   4. 查看完整日志：{log_path}")
            else:
                print(f"   ⚠️  无法读取日志文件")
        except Exception as e:
            print(f"   ⚠️  日志读取失败：{e}")
        
        print(f"\n📋 完整日志路径：{log_path}")
        return 1


def cmd_https(args):
    """设置强制 HTTPS"""
    client = get_client(args.server)

    # 先检查当前 HTTPS 状态
    print(f"🔍 检查 HTTPS 状态...")
    ssl_endpoint = "/site?action=GetSSL"
    ssl_params = {"siteName": args.name}
    ssl_result = client.request(ssl_endpoint, ssl_params)
    
    # 处理不同的返回格式
    https_enabled = False
    if isinstance(ssl_result, dict):
        https_enabled = ssl_result.get('httpTohttps', False)
    elif isinstance(ssl_result, list) and ssl_result:
        https_enabled = ssl_result[0].get('httpTohttps', False) if isinstance(ssl_result[0], dict) else False
    
    if args.enable:
        if https_enabled:
            print(f"ℹ️  强制 HTTPS 已经开启，无需重复操作")
            return 0
        
        endpoint = "/site?action=HttpToHttps"
        action_msg = "已开启"
    elif args.disable:
        if not https_enabled:
            print(f"ℹ️  强制 HTTPS 已经关闭，无需重复操作")
            return 0
        
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


def cmd_deploy(args):
    """部署证书到站点"""
    client = get_client(args.server)

    print(f"\n🔐 正在部署 SSL 证书到站点：{args.name}\n")

    # 步骤 1: 获取证书列表
    print("1️⃣ 获取证书列表...")
    cert_endpoint = "/ssl?action=get_cert_list"
    cert_params = {"search_limit": 0, "search_name": "", "force_refresh": 0}
    cert_result = client.request(cert_endpoint, cert_params)
    
    cert_list = cert_result if isinstance(cert_result, list) else cert_result.get('data', [])
    
    if not cert_list:
        print("   ❌ 未找到可用证书")
        return 1
    
    # 找到匹配的证书
    target_cert = None
    if args.domain:
        for cert in cert_list:
            cert_dns = cert.get('dns', [])
            cert_dns_str = ','.join(cert_dns) if isinstance(cert_dns, list) else str(cert_dns)
            if args.domain in cert_dns_str:
                target_cert = cert
                break
    else:
        # 使用最新证书
        target_cert = cert_list[0] if cert_list else None
    
    if not target_cert:
        print(f"   ❌ 未找到域名 {args.domain} 的证书")
        return 1
    
    ssl_hash = target_cert.get('hash')
    cert_dns = target_cert.get('dns', [])
    cert_name = ', '.join(cert_dns) if isinstance(cert_dns, list) else str(cert_dns)
    
    print(f"   ✅ 找到证书：{cert_name}")
    print(f"   SSL Hash: {ssl_hash}")
    print(f"   有效期：{target_cert.get('notBefore', 'N/A')} ~ {target_cert.get('notAfter', 'N/A')}")

    # 步骤 2: 验证证书链
    print("\n2️⃣ 验证证书链...")
    verify_endpoint = "/ssl/cert/verify_certificate_chain"
    verify_params = {"ssl_hash": ssl_hash}
    verify_result = client.request(verify_endpoint, verify_params)
    
    if verify_result.get('status') or isinstance(verify_result, list):
        print("   ✅ 证书链验证通过")
    else:
        print(f"   ⚠️  证书链验证跳过：{verify_result.get('msg', '')}")

    # 步骤 3: 应用证书到站点
    print("\n3️⃣ 应用证书到站点...")
    deploy_endpoint = "/ssl?action=SetBatchCertToSite"
    batch_info = [{
        "ssl_hash": ssl_hash,
        "siteName": args.name,
        "certName": cert_name
    }]
    deploy_params = {"BatchInfo": json.dumps(batch_info)}
    deploy_result = client.request(deploy_endpoint, deploy_params)
    
    # 检查部署结果（支持不同的返回格式）
    deploy_success = False
    if deploy_result.get('status'):
        deploy_success = True
    elif deploy_result.get('success', 0) > 0:
        deploy_success = True
    
    if deploy_success:
        print(f"   ✅ 证书部署成功")
    else:
        print(f"   ❌ 证书部署失败：{deploy_result.get('msg', '')}")
        return 1

    # 步骤 4: 启用 HTTPS（先检查状态）
    print("\n4️⃣ 检查并启用 HTTPS...")
    ssl_check_endpoint = "/site?action=GetSSL"
    ssl_check_params = {"siteName": args.name}
    ssl_check_result = client.request(ssl_check_endpoint, ssl_check_params)
    
    https_enabled = False
    if isinstance(ssl_check_result, dict):
        https_enabled = ssl_check_result.get('httpTohttps', False)
    elif isinstance(ssl_check_result, list) and ssl_check_result:
        https_enabled = ssl_check_result[0].get('httpTohttps', False) if isinstance(ssl_check_result[0], dict) else False
    
    if https_enabled:
        print(f"   ℹ️  HTTPS 已经启用，跳过")
    else:
        https_endpoint = "/site?action=HttpToHttps"
        https_params = {"siteName": args.name}
        https_result = client.request(https_endpoint, https_params)
        
        if https_result.get('status'):
            print(f"   ✅ HTTPS 已启用")
        else:
            print(f"   ⚠️  HTTPS 启用失败：{https_result.get('msg', '')}")

    print(f"\n🎉 证书部署完成！")
    print(f"   域名：{cert_name}")
    print(f"   站点：{args.name}")
    return 0


def cmd_orders(args):
    """查看证书申请订单列表"""
    client = get_client(args.server)

    # 同时查询 ACME 和 SSL 订单
    print(f"\n📋 SSL 证书订单列表：{args.name}\n")
    
    # ACME 订单
    acme_endpoint = "/acme?action=get_order_list"
    acme_params = {
        "siteName": args.name,
        "status_id": args.status
    }
    acme_result = client.request(acme_endpoint, acme_params)
    
    # 处理不同的返回格式
    if isinstance(acme_result, list):
        acme_orders = acme_result
    elif isinstance(acme_result, dict):
        acme_orders = acme_result.get('data', [])
    else:
        acme_orders = []
    if acme_orders:
        print("🔐 ACME 证书订单:")
        for order in acme_orders:
            status = order.get('status', 0)
            status_text = {
                0: "⏳ 待验证",
                1: "✅ 已签发",
                2: "❌ 已失败",
                3: "🔄 续期中"
            }.get(status, f"未知 ({status})")
            
            domains = order.get('domains', [])
            domain_str = ', '.join(domains) if isinstance(domains, list) else str(domains)
            
            print(f"\n   域名：{domain_str}")
            print(f"   状态：{status_text}")
            print(f"   CA: {order.get('ca_name', 'Unknown')}")
            print(f"   时间：{order.get('addtime', 'N/A')}")
            if order.get('msg'):
                print(f"   消息：{order.get('msg')}")
        print()
    
    # SSL 订单
    ssl_endpoint = "/ssl?action=get_order_list"
    ssl_params = {
        "siteName": args.name
    }
    ssl_result = client.request(ssl_endpoint, ssl_params)
    
    # 处理不同的返回格式
    if isinstance(ssl_result, list):
        ssl_orders = ssl_result
    elif isinstance(ssl_result, dict):
        ssl_orders = ssl_result.get('data', [])
    else:
        ssl_orders = []
    if ssl_orders:
        print("🔐 SSL 证书订单:")
        for order in ssl_orders:
            print(f"\n   域名：{order.get('domain', 'N/A')}")
            print(f"   状态：{order.get('status', 'N/A')}")
            print(f"   时间：{order.get('addtime', 'N/A')}")
        print()
    
    if not acme_orders and not ssl_orders:
        print("   暂无证书订单")
    
    return 0


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
    apply_parser.add_argument('--ca', choices=['letsencrypt', 'litessl'], default='letsencrypt', help='CA 机构')
    apply_parser.add_argument('--auth-type', choices=['http', 'dns'], default='http', help='验证方式')
    apply_parser.add_argument('--wildcard', action='store_true', help='申请通配符证书')
    apply_parser.set_defaults(func=cmd_apply)

    # orders 命令
    orders_parser = subparsers.add_parser('orders', help='查看证书申请订单列表')
    orders_parser.add_argument('-n', '--name', required=True, help='站点域名')
    orders_parser.add_argument('--status', type=int, default=-1, help='状态筛选')
    orders_parser.set_defaults(func=cmd_orders)

    # deploy 命令
    deploy_parser = subparsers.add_parser('deploy', help='部署证书到站点')
    deploy_parser.add_argument('-n', '--name', required=True, help='站点域名')
    deploy_parser.add_argument('-d', '--domain', help='指定域名（不指定则自动匹配最新证书）')
    deploy_parser.set_defaults(func=cmd_deploy)

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
