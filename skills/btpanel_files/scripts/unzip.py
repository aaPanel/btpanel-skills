#!/usr/bin/env python3
"""
宝塔面板文件解压脚本

功能：
- 解压 zip/tar.gz/tar.bz2 文件
- 支持解压密码
- 设置解压后目录权限

API 参考：
- /files?action=UnZip - 解压文件
"""

import sys
import argparse
from pathlib import Path

# 添加父目录到 sys.path 以支持导入 bt_common
_script_dir = Path(__file__).parent
_skill_root = _script_dir.parent
if (_skill_root / "bt_common").exists():
    sys.path.insert(0, str(_skill_root))
else:
    sys.path.insert(0, str(_skill_root.parent))

from bt_common.bt_client import BtClient, BtClientManager
from bt_common.config import get_servers


def get_client(server_name: str = None) -> BtClient:
    """获取宝塔面板客户端"""
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


def get_archive_type(filepath: str) -> str:
    """根据文件扩展名判断压缩类型"""
    filepath = filepath.lower()
    if filepath.endswith('.zip'):
        return 'zip'
    elif filepath.endswith('.tar.gz') or filepath.endswith('.tgz'):
        return 'tar.gz'
    elif filepath.endswith('.tar.bz2') or filepath.endswith('.tbz2'):
        return 'tar.bz2'
    elif filepath.endswith('.tar'):
        return 'tar'
    elif filepath.endswith('.gz'):
        return 'gz'
    elif filepath.endswith('.bz2'):
        return 'bz2'
    elif filepath.endswith('.rar'):
        return 'rar'
    elif filepath.endswith('.7z'):
        return '7z'
    else:
        return 'zip'  # 默认 zip


def format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f}KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f}MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f}GB"


def cmd_unzip(args):
    """解压文件"""
    client = get_client(args.server)
    
    # 自动检测压缩类型
    archive_type = args.type or get_archive_type(args.source)
    
    print(f"\n📤 解压文件...")
    print(f"   源文件: {args.source}")
    print(f"   目标目录: {args.dest}")
    print(f"   压缩类型: {archive_type}")
    if args.password:
        print(f"   解压密码: {'*' * len(args.password)}")
    print(f"   目录权限: {args.permission}")
    print()
    
    endpoint = "/files?action=UnZip"
    params = {
        "sfile": args.source,
        "dfile": args.dest,
        "type": archive_type,
        "coding": args.coding,
        "password": args.password or "",
        "power": args.permission
    }
    
    try:
        result = client.request(endpoint, params)
        
        if result.get('status'):
            print(f"✅ {result.get('msg', '文件解压成功!')}")
            print(f"   解压路径: {args.dest}")
            return 0
        else:
            print(f"❌ 解压失败：{result.get('msg', '未知错误')}")
            return 1
            
    except Exception as e:
        print(f"❌ 请求失败：{e}")
        return 1


def cmd_info(args):
    """查看压缩包信息（预览内容）"""
    client = get_client(args.server)
    
    # 获取文件信息
    endpoint = "/files?action=GetFileBody"
    params = {
        "path": args.source
    }
    
    print(f"\n📦 压缩包信息: {args.source}")
    print("-" * 50)
    
    # 由于 API 可能不支持预览，我们先显示基本信息
    archive_type = get_archive_type(args.source)
    print(f"   压缩类型: {archive_type}")
    print(f"   文件路径: {args.source}")
    print()
    print("💡 使用 unzip 命令解压此文件")


def cmd_support(args):
    """显示支持的压缩格式"""
    print("\n📦 支持的压缩格式:")
    print("-" * 50)
    
    formats = [
        ("zip", "ZIP 压缩包", "最常用"),
        ("tar.gz", "Gzip 压缩包", "Linux 常用"),
        ("tar.bz2", "Bzip2 压缩包", "压缩率高"),
        ("tar", "TAR 归档", "无压缩归档"),
        ("gz", "Gzip 单文件", "单文件压缩"),
        ("bz2", "Bzip2 单文件", "单文件压缩"),
        ("rar", "RAR 压缩包", "需要 unrar"),
        ("7z", "7-Zip 压缩包", "高压缩率"),
    ]
    
    for fmt, name, note in formats:
        print(f"   {fmt:<10} {name:<20} ({note})")
    
    print()
    print("💡 自动检测：根据文件扩展名自动识别压缩类型")


def main():
    parser = argparse.ArgumentParser(
        description="宝塔面板文件解压工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 解压 WordPress（自动检测类型）
  python3 unzip.py -s "内网 172" unzip \\
      --source "/www/test/wordpress.zip" \\
      --dest "/www/test"

  # 解压带密码的压缩包
  python3 unzip.py -s "内网 172" unzip \\
      --source "/www/test/protected.zip" \\
      --dest "/www/test" \\
      --password "mypassword"

  # 解压 tar.gz 并设置权限
  python3 unzip.py -s "内网 172" unzip \\
      --source "/www/test/backup.tar.gz" \\
      --dest "/www/backup" \\
      --permission 755

  # 查看支持的格式
  python3 unzip.py support
        """
    )
    
    # 全局参数
    parser.add_argument('-s', '--server', help='服务器名称')
    
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # unzip 命令
    unzip_parser = subparsers.add_parser('unzip', help='解压文件')
    unzip_parser.add_argument('--source', required=True, help='源文件路径（压缩包路径）')
    unzip_parser.add_argument('--dest', required=True, help='目标目录（解压到哪）')
    unzip_parser.add_argument('--type', choices=['zip', 'tar.gz', 'tar.bz2', 'tar', 'gz', 'bz2', 'rar', '7z'],
                              help='压缩类型（自动检测）')
    unzip_parser.add_argument('--password', help='解压密码（如果有）')
    unzip_parser.add_argument('--coding', default='UTF-8', help='文件名编码（默认 UTF-8）')
    unzip_parser.add_argument('--permission', default='755', help='解压后目录权限（默认 755）')
    unzip_parser.set_defaults(func=cmd_unzip)
    
    # info 命令
    info_parser = subparsers.add_parser('info', help='查看压缩包信息')
    info_parser.add_argument('--source', required=True, help='压缩包路径')
    info_parser.set_defaults(func=cmd_info)
    
    # support 命令
    support_parser = subparsers.add_parser('support', help='显示支持的压缩格式')
    support_parser.set_defaults(func=cmd_support)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())