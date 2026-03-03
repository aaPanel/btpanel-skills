#!/usr/bin/env python3
# /// script
# dependencies = []
# ///
"""
技能打包脚本
将技能打包为独立可用的压缩包，包含公共模块

目录结构:
- src/         : 源码目录（开发时使用）
- skills/      : 打包输出目录（打包后存放）
"""

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 源码目录
SRC_DIR = PROJECT_ROOT / "src"

# 输出目录
OUTPUT_DIR = PROJECT_ROOT / "skills"

# 技能定义
SKILLS = {
    "btpanel": {
        "name": "btpanel",
        "description": "宝塔面板(BT-Panel)运维监控技能，提供服务器资源监控、网站状态检查、服务状态检查、SSH安全审计、计划任务管理、日志读取等功能",
        "scripts": [
            "monitor.py",
            "sites.py",
            "services.py",
            "logs.py",
            "ssh.py",
            "crontab.py",
            "bt-config.py",
        ],
    },
}

# 公共模块
COMMON_MODULE = "bt_common"


def clean_output_dir(output_dir: Path, skill_name: str):
    """清理指定技能的输出目录"""
    skill_output = output_dir / skill_name
    if skill_output.exists():
        shutil.rmtree(skill_output)
    skill_output.mkdir(parents=True, exist_ok=True)
    print(f"✓ 清理并创建输出目录: {skill_output}")


def copy_common_module(target_dir: Path):
    """复制公共模块到目标目录"""
    common_src = SRC_DIR / COMMON_MODULE
    common_dst = target_dir / COMMON_MODULE

    if common_dst.exists():
        shutil.rmtree(common_dst)

    if not common_src.exists():
        print(f"  ✗ 公共模块源目录不存在: {common_src}")
        return False

    # 复制时排除 __pycache__ 目录
    shutil.copytree(common_src, common_dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"))
    print(f"  ✓ 复制公共模块: {COMMON_MODULE}/")
    return True


def copy_icons(target_dir: Path):
    """复制图标资源到目标目录"""
    icons_src = PROJECT_ROOT / "icon"
    icons_dst = target_dir / "icon"

    if not icons_src.exists():
        print(f"  ⚠ 图标目录不存在: {icons_src}")
        return

    if icons_dst.exists():
        shutil.rmtree(icons_dst)

    shutil.copytree(icons_src, icons_dst)
    icon_files = list(icons_dst.glob("*"))
    print(f"  ✓ 复制图标资源: icon/ ({len(icon_files)} 个文件)")


def copy_scripts(scripts: list, scripts_src_dir: Path, scripts_dst_dir: Path) -> int:
    """复制多个脚本文件"""
    copied = 0
    for script_name in scripts:
        script_src = scripts_src_dir / script_name
        if script_src.exists():
            script_dst = scripts_dst_dir / script_name
            shutil.copy(script_src, script_dst)
            script_dst.chmod(0o755)
            print(f"  ✓ 复制脚本: scripts/{script_name}")
            copied += 1
        else:
            print(f"  ⚠ 脚本不存在: scripts/{script_name}")
    return copied


def build_single_skill(skill_name: str, output_dir: Path, create_zip: bool = True, zip_format: str = "zip") -> Optional[Path]:
    """构建单个技能包"""
    if skill_name not in SKILLS:
        print(f"✗ 未知的技能: {skill_name}")
        return None

    skill_info = SKILLS[skill_name]
    skill_src_dir = SRC_DIR / skill_name

    if not skill_src_dir.exists():
        print(f"✗ 技能源码目录不存在: {skill_src_dir}")
        return None

    print(f"\n构建技能: {skill_name}")
    print(f"  描述: {skill_info['description']}")

    # 清理并创建输出目录
    clean_output_dir(output_dir, skill_name)
    skill_output_dir = output_dir / skill_name

    # 1. 复制 SKILL.md
    skill_md = skill_src_dir / "SKILL.md"
    if skill_md.exists():
        shutil.copy(skill_md, skill_output_dir / "SKILL.md")
        print(f"  ✓ 复制 SKILL.md")

    # 2. 创建 scripts 目录并复制脚本
    scripts_dir = skill_output_dir / "scripts"
    scripts_dir.mkdir(exist_ok=True)

    scripts_src_dir = skill_src_dir / "scripts"
    scripts = skill_info.get("scripts", [])

    if scripts:
        copied = copy_scripts(scripts, scripts_src_dir, scripts_dir)
        if copied == 0:
            print(f"  ✗ 没有找到任何脚本")
            return None
    else:
        # 兼容旧的单脚本定义
        single_script = skill_info.get("script")
        if single_script:
            script_src = scripts_src_dir / single_script
            if script_src.exists():
                copy_scripts([single_script], scripts_src_dir, scripts_dir)
            else:
                print(f"  ✗ 脚本不存在: {single_script}")
                return None

    # 3. 复制公共模块
    if not copy_common_module(skill_output_dir):
        return None

    # 4. 复制图标资源
    copy_icons(skill_output_dir)

    # 5. 创建 README
    scripts_list = skill_info.get("scripts", [])
    main_script = scripts_list[0] if scripts_list else "monitor.py"

    readme_content = f"""# {skill_info['name']}

{skill_info['description']}

## 版本要求

- **宝塔面板**: >= 9.0.0
- **Python**: >= 3.10

## 快速开始

1. 安装依赖:
   ```bash
   pip install requests pyyaml rich
   ```

2. 配置服务器:
   ```bash
   # 使用配置工具添加服务器
   python3 scripts/bt-config.py add --name prod-01 --host https://panel.example.com:8888 --token YOUR_TOKEN

   # 查看配置
   python3 scripts/bt-config.py list
   ```

   或手动编辑配置文件 `~/.openclaw/bt-skills.yaml`

3. 运行:
   ```bash
   # 查看帮助
   python3 scripts/{main_script} --help

   # 监控所有服务器
   python3 scripts/{main_script}
   ```

## 可用脚本

| 脚本 | 功能 |
|------|------|
| monitor.py | 系统资源监控 |
| sites.py | 网站状态检查 |
| services.py | 服务状态检查 |
| logs.py | 日志读取 |
| ssh.py | SSH状态和登录日志 |
| crontab.py | 计划任务检查 |
| bt-config.py | 配置管理工具 |

## 配置管理工具

```bash
# 初始化配置
python3 scripts/bt-config.py init

# 列出服务器
python3 scripts/bt-config.py list

# 添加服务器
python3 scripts/bt-config.py add -n prod-01 -H https://panel.example.com:8888 -t YOUR_TOKEN

# 更新服务器
python3 scripts/bt-config.py update prod-01 --disabled

# 删除服务器
python3 scripts/bt-config.py remove prod-01

# 设置阈值
python3 scripts/bt-config.py threshold --cpu 75 --memory 80

# 查看配置路径
python3 scripts/bt-config.py path
```

详细使用说明请参考 SKILL.md
"""
    (skill_output_dir / "README.md").write_text(readme_content, encoding="utf-8")
    print(f"  ✓ 创建 README.md")

    # 6. 创建压缩包
    if create_zip:
        return create_archive(skill_output_dir, output_dir, zip_format)

    return skill_output_dir


def create_archive(skill_dir: Path, output_dir: Path, format: str = "zip") -> Optional[Path]:
    """创建压缩包"""
    if format == "zip":
        archive_path = shutil.make_archive(
            str(skill_dir),  # 基础名称（不含扩展名）
            "zip",
            skill_dir.parent,  # 根目录
            skill_dir.name,  # 要打包的目录名
        )
        print(f"  ✓ 创建压缩包: {archive_path}")
        return Path(archive_path)
    elif format == "tar.gz":
        archive_path = shutil.make_archive(
            str(skill_dir),
            "gztar",
            skill_dir.parent,
            skill_dir.name,
        )
        print(f"  ✓ 创建压缩包: {archive_path}")
        return Path(archive_path)
    else:
        print(f"  ✗ 不支持的格式: {format}")
        return None


def build_all_skills(output_dir: Path, create_zip: bool = True, zip_format: str = "zip") -> list:
    """构建所有技能"""
    built_skills = []

    for skill_name in SKILLS:
        skill_dir = build_single_skill(skill_name, output_dir, create_zip, zip_format)
        if skill_dir:
            built_skills.append(skill_name)

    return built_skills


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="宝塔面板运维监控技能打包工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 打包所有技能
  python3 scripts/build_skills.py

  # 打包单个技能
  python3 scripts/build_skills.py --skill btpanel

  # 打包并创建 tar.gz 格式
  python3 scripts/build_skills.py --format tar.gz

  # 只构建目录，不创建压缩包
  python3 scripts/build_skills.py --no-zip

目录结构:
  src/         - 源码目录（开发时使用）
  skills/      - 打包输出目录（打包后存放）
        """,
    )

    parser.add_argument(
        "--skill", "-s",
        choices=list(SKILLS.keys()) + ["all"],
        default="all",
        help="指定要打包的技能，默认打包所有",
    )
    parser.add_argument(
        "--format", "-f",
        choices=["zip", "tar.gz"],
        default="zip",
        help="压缩包格式，默认 zip",
    )
    parser.add_argument(
        "--no-zip",
        action="store_true",
        help="只构建目录，不创建压缩包",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help=f"输出目录，默认 {OUTPUT_DIR.relative_to(PROJECT_ROOT)}",
    )

    args = parser.parse_args()

    # 输出目录
    output_dir = Path(args.output) if args.output else OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("宝塔面板运维监控技能打包工具")
    print("=" * 60)
    print(f"源码目录: {SRC_DIR}")
    print(f"输出目录: {output_dir}")
    print(f"压缩格式: {args.format if not args.no_zip else '不压缩'}")

    # 构建
    if args.skill == "all":
        built = build_all_skills(output_dir, create_zip=not args.no_zip, zip_format=args.format)
    else:
        skill_dir = build_single_skill(args.skill, output_dir, create_zip=not args.no_zip, zip_format=args.format)
        built = [args.skill] if skill_dir else []

    # 输出结果
    print("\n" + "=" * 60)
    print("构建完成!")
    print("=" * 60)

    # 列出生成的文件
    print("\n生成的文件:")
    for item in sorted(output_dir.iterdir()):
        if item.is_dir():
            print(f"  📁 {item.name}/")
        else:
            size = item.stat().st_size
            if size > 1024 * 1024:
                size_str = f"{size / 1024 / 1024:.1f} MB"
            elif size > 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size} B"
            print(f"  📄 {item.name} ({size_str})")

    print(f"\n成功构建 {len(built)} 个技能!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
