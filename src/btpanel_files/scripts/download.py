#!/usr/bin/env python3
"""
宝塔面板文件下载脚本

功能：
- 从 URL 下载文件到服务器指定目录
- 支持等待下载完成
- 显示下载进度

API 参考：
- /files?action=DownloadFile - 发起下载
- /task?action=get_task_lists - 查询任务进度
"""

import sys
import time
import json
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


def format_time(seconds: int) -> str:
    """格式化时间"""
    if seconds < 60:
        return f"{seconds}秒"
    elif seconds < 3600:
        return f"{seconds // 60}分{seconds % 60}秒"
    else:
        return f"{seconds // 3600}小时{(seconds % 3600) // 60}分"


def cmd_download(args):
    """下载文件"""
    client = get_client(args.server)
    
    # 自动提取文件名（如果未指定）
    filename = args.filename
    if not filename:
        # 使用 urllib 解析 URL
        from urllib.parse import urlparse
        parsed = urlparse(args.url)
        # 从 path 中提取文件名
        path_parts = parsed.path.rstrip('/').split('/')
        filename = path_parts[-1] if path_parts and path_parts[-1] else 'downloaded_file'
    
    # 1. 发起下载请求
    print(f"\n📥 开始下载文件...")
    print(f"   URL: {args.url}")
    print(f"   目标路径: {args.path}")
    print(f"   文件名: {filename}")
    print()
    
    endpoint = "/files?action=DownloadFile"
    # 注意：filename 是必传参数，否则 API 返回 500
    params = {
        "url": args.url,
        "path": args.path,
        "filename": filename,  # 必传！
    }
    
    try:
        result = client.request(endpoint, params)
        if result.get('status'):
            print(f"✅ 下载任务已添加到队列")
        else:
            print(f"❌ 添加下载任务失败：{result.get('msg', '未知错误')}")
            return 1
    except Exception as e:
        print(f"❌ 请求失败：{e}")
        return 1
    
    # 2. 如果不需要等待，直接返回
    if not args.wait:
        print("\n💡 使用 --wait 参数可以等待下载完成")
        return 0
    
    # 3. 等待下载完成
    print("\n⏳ 等待下载完成...")
    print("-" * 60)
    
    task_id = None
    last_progress = -1
    start_time = time.time()
    timeout = args.timeout or 600  # 默认 10 分钟超时
    
    while True:
        elapsed = time.time() - start_time
        if elapsed > timeout:
            print(f"\n❌ 下载超时（{timeout}秒）")
            return 1
        
        # 查询任务列表
        try:
            task_result = client.request("/task?action=get_task_lists", {"status": "-3"})
            tasks = task_result if isinstance(task_result, list) else []
            
            # 找到下载任务
            download_task = None
            for task in tasks:
                if task.get('type') == '1' and args.url in task.get('shell', ''):
                    download_task = task
                    task_id = task.get('id')
                    break
            
            if not download_task:
                # 任务可能已完成，检查文件是否存在
                time.sleep(1)
                continue
            
            # 显示进度
            log = download_task.get('log', {})
            if isinstance(log, str):
                try:
                    log = json.loads(log) if log else {}
                except:
                    log = {}
            
            # 安全获取数值，处理字符串类型
            def safe_int(val, default=0):
                try:
                    return int(float(val)) if val else default
                except (ValueError, TypeError):
                    return default
            
            def safe_float(val, default=0.0):
                try:
                    return float(val) if val else default
                except (ValueError, TypeError):
                    return default
            
            progress = safe_float(log.get('pre', 0), 0)
            speed = safe_int(log.get('speed', 0), 0)
            used = safe_int(log.get('used', 0), 0)
            total = safe_int(log.get('total', 0), 0)
            remaining = safe_int(log.get('time', 0), 0)
            status = download_task.get('status')
            
            # 构建进度条
            bar_length = 40
            filled = int(bar_length * progress / 100)
            bar = '█' * filled + '░' * (bar_length - filled)
            
            # 只在进度变化时更新显示
            if progress != last_progress:
                last_progress = progress
                print(f"\r   [{bar}] {progress:.1f}% | "
                      f"{format_size(used)}/{format_size(total) if total else '???'} | "
                      f"{format_size(speed)}/s | "
                      f"剩余: {format_time(remaining)} | "
                      f"状态: {'下载中' if status == -1 else '等待中' if status == 0 else '已完成'}", 
                      end='', flush=True)
            
            # 检查是否完成
            if status == 1 or progress >= 100:
                print()  # 换行
                print("-" * 60)
                print(f"✅ 下载完成！")
                print(f"   文件: {args.path}/{filename}")
                print(f"   大小: {format_size(total) if total else '未知'}")
                print(f"   耗时: {format_time(int(elapsed))}")
                return 0
            
            # 检查是否失败
            if status == -2:
                print()  # 换行
                print("-" * 60)
                print(f"❌ 下载失败")
                return 1
            
            time.sleep(1)  # 每秒刷新一次
            
        except Exception as e:
            print(f"\n❌ 查询进度失败：{e}")
            time.sleep(2)


def cmd_tasks(args):
    """查看任务列表"""
    client = get_client(args.server)
    
    endpoint = "/task?action=get_task_lists"
    params = {"status": args.status if hasattr(args, 'status') else "-3"}
    
    try:
        result = client.request(endpoint, params)
        tasks = result if isinstance(result, list) else []
        
        if not tasks:
            print("📭 暂无任务")
            return 0
        
        print(f"\n📋 任务列表 (共 {len(tasks)} 个)")
        print("-" * 80)
        print(f"{'ID':<6} {'类型':<10} {'名称':<20} {'状态':<10} {'进度':<10}")
        print("-" * 80)
        
        status_map = {
            -2: "❌ 失败",
            -1: "⏳ 执行中",
            0: "⏸️ 等待中",
            1: "✅ 已完成"
        }
        
        type_map = {
            "1": "下载文件",
            "2": "解压文件",
            "3": "压缩文件"
        }
        
        for task in tasks:
            task_id = task.get('id', 'N/A')
            task_type = type_map.get(str(task.get('type', '')), '未知')
            task_name = task.get('name', 'N/A')[:18]
            task_status = status_map.get(task.get('status'), '未知')
            
            log = task.get('log', {})
            if isinstance(log, str):
                log = {}
            progress = f"{log.get('pre', 0):.1f}%" if log else 'N/A'
            
            print(f"{task_id:<6} {task_type:<10} {task_name:<20} {task_status:<10} {progress:<10}")
        
        print("-" * 80)
        return 0
        
    except Exception as e:
        print(f"❌ 查询失败：{e}")
        return 1


def cmd_cancel(args):
    """取消任务"""
    client = get_client(args.server)
    
    endpoint = "/task?action=remove_task"
    params = {"id": args.task_id}
    
    try:
        result = client.request(endpoint, params)
        if result.get('status'):
            print(f"✅ 任务 {args.task_id} 已取消")
            return 0
        else:
            print(f"❌ 取消失败：{result.get('msg', '未知错误')}")
            return 1
    except Exception as e:
        print(f"❌ 请求失败：{e}")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="宝塔面板文件下载工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 下载 WordPress 到指定目录（等待完成）
  python3 download.py -s "内网 172" download \\
      --url "https://cn.wordpress.org/latest-zh_CN.zip" \\
      --path "/www/test" \\
      --filename "wordpress.zip" \\
      --wait

  # 查看当前任务列表
  python3 download.py -s "内网 172" tasks

  # 取消任务
  python3 download.py -s "内网 172" cancel --task-id 1
        """
    )
    
    # 全局参数
    parser.add_argument('-s', '--server', help='服务器名称')
    
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # download 命令
    download_parser = subparsers.add_parser('download', help='下载文件')
    download_parser.add_argument('--url', required=True, help='下载 URL')
    download_parser.add_argument('--path', required=True, help='目标路径')
    download_parser.add_argument('--filename', help='保存文件名（可选，默认从 URL 提取）')
    download_parser.add_argument('--wait', action='store_true', help='等待下载完成')
    download_parser.add_argument('--timeout', type=int, default=600, help='超时时间（秒，默认 600）')
    download_parser.set_defaults(func=cmd_download)
    
    # tasks 命令
    tasks_parser = subparsers.add_parser('tasks', help='查看任务列表')
    tasks_parser.add_argument('--status', default='-3', help='任务状态（-3=全部，-1=执行中，0=等待中，1=已完成）')
    tasks_parser.set_defaults(func=cmd_tasks)
    
    # cancel 命令
    cancel_parser = subparsers.add_parser('cancel', help='取消任务')
    cancel_parser.add_argument('--task-id', required=True, type=int, help='任务 ID')
    cancel_parser.set_defaults(func=cmd_cancel)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())