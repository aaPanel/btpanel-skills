#!/usr/bin/env python3
# coding: utf-8
"""
宝塔文件操作 CLI 工具
提供基本的文件管理命令
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# 兼容开发环境和发布环境的导入
# 发布环境：bt_common/ (脚本在 scripts/)
# 开发环境：src/bt_common/ (脚本在 src/btpanel_files/scripts/)
_skill_root = Path(__file__).parent.parent  # 技能包根目录

# 优先尝试发布环境（技能包根目录），然后尝试开发环境
if (_skill_root / "bt_common").exists():
    sys.path.insert(0, str(_skill_root))
else:
    sys.path.insert(0, str(_skill_root.parent / "src"))

from bt_common.utils import format_bytes, format_timestamp


def format_size(size: int, is_dir: bool = False) -> str:
    """格式化文件大小显示"""
    if is_dir:
        # 目录大小通常是 KB
        if size >= 1024 * 1024:
            return f"{size / (1024 * 1024):.1f}GB"
        elif size >= 1024:
            return f"{size / 1024:.1f}MB"
        else:
            return f"{size}KB"
    else:
        # 文件大小是字节
        if size >= 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024 * 1024):.1f}GB"
        elif size >= 1024 * 1024:
            return f"{size / (1024 * 1024):.1f}MB"
        elif size >= 1024:
            return f"{size / 1024:.1f}KB"
        else:
            return f"{size}B"


def format_time(timestamp: int) -> str:
    """格式化时间戳"""
    try:
        return datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
    except:
        return str(timestamp)


def cmd_ls(args):
    """列出目录内容"""
    from bt_common.files_client import FilesClient

    client = FilesClient(args.server)
    result = client.get_dir(args.path, args.page, args.rows)

    if 'error' in result:
        print(f"错误：{result['error']}")
        return 1

    # 打印路径
    print(f"\n📁 {result.get('path', args.path)}\n")

    # 打印目录列表
    dirs = result.get('dir', [])
    files = result.get('files', [])

    if dirs:
        print("  目录:")
        for d in dirs:
            name = d.get('nm', 'unknown')
            size = format_size(d.get('sz', 0), is_dir=True)
            mtime = format_time(d.get('mt', 0))
            acc = d.get('acc', '---')
            user = d.get('user', 'unknown')
            print(f"    📁 {name:<30} {size:>8}  {acc:<5}  {user:<10}  {mtime}")

    if files:
        print("\n  文件:")
        for f in files:
            name = f.get('nm', 'unknown')
            size = format_size(f.get('sz', 0), is_dir=False)
            mtime = format_time(f.get('mt', 0))
            acc = f.get('acc', '---')
            user = f.get('user', 'unknown')
            # 显示备注（如果有）
            rmk = f.get('rmk', '')
            rmk_str = f"  # {rmk}" if rmk else ""
            print(f"    📄 {name:<30} {size:>8}  {acc:<5}  {user:<10}  {mtime}{rmk_str}")

    if not dirs and not files:
        print("  (空目录)")

    # 打印分页信息
    page_info = result.get('page', '')
    if page_info:
        print(f"\n  {page_info}")

    return 0


def cmd_cat(args):
    """读取文件内容"""
    from bt_common.files_client import FilesClient

    client = FilesClient(args.server)
    result = client.get_file_body(args.path)

    if not result.get('status') and not result.get('only_read') == False:
        print(f"错误：{result.get('msg', '读取失败')}")
        return 1

    data = result.get('data', '')

    if args.lines:
        # 只显示最后 N 行
        lines = data.split('\n')
        data = '\n'.join(lines[-args.lines:])

    print(data)

    # 显示文件信息
    if args.verbose:
        print(f"\n--- 文件信息 ---", file=sys.stderr)
        print(f"大小：{format_bytes(result.get('size', 0))}", file=sys.stderr)
        print(f"编码：{result.get('encoding', 'utf-8')}", file=sys.stderr)
        print(f"只读：{'是' if result.get('only_read') else '否'}", file=sys.stderr)

    return 0


def cmd_edit(args):
    """编辑文件内容"""
    from bt_common.files_client import FilesClient

    client = FilesClient(args.server)

    # 如果指定了内容参数
    if args.content:
        content = args.content
    elif args.file:
        # 从文件读取内容
        with open(args.file, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        # 从标准输入读取
        content = sys.stdin.read()

    # 获取当前文件的 st_mtime
    try:
        file_info = client.get_file_body(args.path)
        st_mtime = file_info.get('st_mtime')
    except:
        st_mtime = None

    result = client.save_file_body(args.path, content, args.encoding, st_mtime)

    if result.get('status'):
        print(f"✅ 文件已保存：{args.path}")
        return 0
    else:
        print(f"❌ 保存失败：{result.get('msg', '未知错误')}")
        return 1


def cmd_mkdir(args):
    """创建目录"""
    from bt_common.files_client import FilesClient

    client = FilesClient(args.server)
    result = client.create_dir(args.path)

    if result.get('status'):
        print(f"✅ 目录已创建：{args.path}")
        return 0
    else:
        print(f"❌ 创建失败：{result.get('msg', '未知错误')}")
        return 1


def cmd_touch(args):
    """创建文件"""
    from bt_common.files_client import FilesClient

    client = FilesClient(args.server)
    result = client.create_file(args.path)

    if result.get('status'):
        print(f"✅ 文件已创建：{args.path}")
        return 0
    else:
        print(f"❌ 创建失败：{result.get('msg', '未知错误')}")
        return 1


def cmd_rm(args):
    """删除文件"""
    from bt_common.files_client import FilesClient

    client = FilesClient(args.server)
    result = client.delete_file(args.path)

    if result.get('status'):
        msg = result.get('msg', '已删除')
        print(f"✅ {msg}: {args.path}")
        return 0
    else:
        print(f"❌ 删除失败：{result.get('msg', '未知错误')}")
        return 1


def cmd_rmdir(args):
    """删除目录"""
    from bt_common.files_client import FilesClient

    client = FilesClient(args.server)
    result = client.delete_dir(args.path)

    if result.get('status'):
        msg = result.get('msg', '已删除')
        print(f"✅ {msg}: {args.path}")
        return 0
    else:
        print(f"❌ 删除失败：{result.get('msg', '未知错误')}")
        return 1


def cmd_stat(args):
    """查看文件权限"""
    from bt_common.files_client import FilesClient

    client = FilesClient(args.server)
    result = client.get_file_access(args.path)

    if 'chmod' in result and 'chown' in result:
        print(f"文件：{args.path}")
        print(f"权限：{result['chmod']}")
        print(f"所有者：{result['chown']}")
        return 0
    else:
        print(f"❌ 获取失败：{result.get('msg', '未知错误')}")
        return 1


def cmd_chmod(args):
    """设置文件权限"""
    from bt_common.files_client import FilesClient

    client = FilesClient(args.server)
    result = client.set_file_access(
        args.path,
        args.access,
        user=args.user,
        group=args.group,
        all_files=args.recursive
    )

    if result.get('status'):
        print(f"✅ 权限已设置：{args.path} -> {args.access}")
        return 0
    else:
        print(f"❌ 设置失败：{result.get('msg', '未知错误')}")
        return 1


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='宝塔文件操作工具',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '-s', '--server',
        help='服务器名称（使用 bt-config 配置的名称）'
    )

    subparsers = parser.add_subparsers(dest='command', help='命令')

    # ls 命令 - 列出目录
    ls_parser = subparsers.add_parser('ls', help='列出目录内容')
    ls_parser.add_argument('path', nargs='?', default='/www', help='目录路径')
    ls_parser.add_argument('-p', '--page', type=int, default=1, help='页码')
    ls_parser.add_argument('-r', '--rows', type=int, default=500, help='每页显示数量')
    ls_parser.set_defaults(func=cmd_ls)

    # cat 命令 - 读取文件
    cat_parser = subparsers.add_parser('cat', help='读取文件内容')
    cat_parser.add_argument('path', help='文件路径')
    cat_parser.add_argument('-n', '--lines', type=int, help='显示最后 N 行')
    cat_parser.add_argument('-v', '--verbose', action='store_true', help='显示文件信息')
    cat_parser.set_defaults(func=cmd_cat)

    # edit 命令 - 编辑文件
    edit_parser = subparsers.add_parser('edit', help='编辑文件内容')
    edit_parser.add_argument('path', help='文件路径')
    edit_parser.add_argument('content', nargs='?', help='文件内容')
    edit_parser.add_argument('-f', '--file', help='从文件读取内容')
    edit_parser.add_argument('-e', '--encoding', default='utf-8', help='文件编码')
    edit_parser.set_defaults(func=cmd_edit)

    # mkdir 命令 - 创建目录
    mkdir_parser = subparsers.add_parser('mkdir', help='创建目录')
    mkdir_parser.add_argument('path', help='目录路径')
    mkdir_parser.set_defaults(func=cmd_mkdir)

    # touch 命令 - 创建文件
    touch_parser = subparsers.add_parser('touch', help='创建文件')
    touch_parser.add_argument('path', help='文件路径')
    touch_parser.set_defaults(func=cmd_touch)

    # rm 命令 - 删除文件
    rm_parser = subparsers.add_parser('rm', help='删除文件')
    rm_parser.add_argument('path', help='文件路径')
    rm_parser.set_defaults(func=cmd_rm)

    # rmdir 命令 - 删除目录
    rmdir_parser = subparsers.add_parser('rmdir', help='删除目录')
    rmdir_parser.add_argument('path', help='目录路径')
    rmdir_parser.set_defaults(func=cmd_rmdir)

    # stat 命令 - 查看权限
    stat_parser = subparsers.add_parser('stat', help='查看文件权限')
    stat_parser.add_argument('path', help='文件路径')
    stat_parser.set_defaults(func=cmd_stat)

    # chmod 命令 - 设置权限
    chmod_parser = subparsers.add_parser('chmod', help='设置文件权限')
    chmod_parser.add_argument('access', help='权限码（如 755, 644）')
    chmod_parser.add_argument('path', help='文件路径')
    chmod_parser.add_argument('-u', '--user', help='所有者用户名', default='www')
    chmod_parser.add_argument('-g', '--group', help='用户组名', default='www')
    chmod_parser.add_argument('-R', '--recursive', action='store_true', help='递归设置子目录和文件')
    chmod_parser.set_defaults(func=cmd_chmod)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
