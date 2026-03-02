#!/usr/bin/env python3
# /// script
# dependencies = []
# ///
"""
技能打包脚本
将技能打包为独立可用的压缩包，包含公共模块
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

# 技能定义
SKILLS = {
    "bt-system-monitor": {
        "name": "bt-system-monitor",
        "description": "系统资源监控技能",
        "script": "monitor.py",
    },
    "bt-security-check": {
        "name": "bt-security-check",
        "description": "安全事件巡检技能",
        "script": "security.py",
    },
    "bt-health-check": {
        "name": "bt-health-check",
        "description": "服务健康检查技能",
        "script": "health.py",
    },
}

# 公共模块
COMMON_MODULE = "bt_common"


def clean_dist(dist_dir: Path):
    """清理 dist 目录"""
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    dist_dir.mkdir(parents=True, exist_ok=True)
    print(f"✓ 清理并创建输出目录: {dist_dir}")


def copy_common_module(target_dir: Path):
    """复制公共模块到目标目录"""
    common_src = PROJECT_ROOT / "skills" / COMMON_MODULE
    common_dst = target_dir / COMMON_MODULE

    if common_dst.exists():
        shutil.rmtree(common_dst)

    shutil.copytree(common_src, common_dst)
    print(f"  ✓ 复制公共模块: {COMMON_MODULE}/")


def create_config_example(target_dir: Path):
    """创建配置示例"""
    config_dir = target_dir / "config"
    config_dir.mkdir(exist_ok=True)

    src = PROJECT_ROOT / "config" / "servers.yaml"
    dst = config_dir / "servers.yaml.example"

    if src.exists():
        shutil.copy(src, dst)
        print(f"  ✓ 创建配置示例: config/servers.yaml.example")
    else:
        # 创建默认配置
        default_config = """# 宝塔面板服务器配置
# 宝塔面板版本要求: >= 9.0.0
# 请复制此文件为 servers.local.yaml 并填入实际密钥
# 或使用全局配置: ~/.openclaw/bt-skills.yaml

servers:
  - name: "server-1"
    host: "https://your-panel.com:8888"
    token: "YOUR_API_TOKEN"
    timeout: 10000
    enabled: true

global:
  retryCount: 3
  retryDelay: 1000
  concurrency: 3
  thresholds:
    cpu: 80
    memory: 85
    disk: 90
"""
        dst.write_text(default_config, encoding="utf-8")
        print(f"  ✓ 创建默认配置示例: config/servers.yaml.example")


def copy_script(script_path: Path, target_dir: Path) -> bool:
    """复制脚本文件（直接复制，不做修改）"""
    script_dst = target_dir / script_path.name
    shutil.copy(script_path, script_dst)
    script_dst.chmod(0o755)
    return True


def build_single_skill(skill_name: str, dist_dir: Path) -> Optional[Path]:
    """构建单个技能包"""
    if skill_name not in SKILLS:
        print(f"✗ 未知的技能: {skill_name}")
        return None

    skill_info = SKILLS[skill_name]
    skill_dir = PROJECT_ROOT / "skills" / skill_name

    if not skill_dir.exists():
        print(f"✗ 技能目录不存在: {skill_dir}")
        return None

    # 创建输出目录
    output_dir = dist_dir / skill_name
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n构建技能: {skill_name}")
    print(f"  描述: {skill_info['description']}")

    # 1. 复制 SKILL.md
    skill_md = skill_dir / "SKILL.md"
    if skill_md.exists():
        shutil.copy(skill_md, output_dir / "SKILL.md")
        print(f"  ✓ 复制 SKILL.md")

    # 2. 创建 scripts 目录并复制脚本
    scripts_dir = output_dir / "scripts"
    scripts_dir.mkdir(exist_ok=True)

    script_src = skill_dir / "scripts" / skill_info["script"]
    if script_src.exists():
        # 直接复制脚本（脚本已包含兼容两种环境的导入）
        copy_script(script_src, scripts_dir)
        print(f"  ✓ 复制脚本: scripts/{skill_info['script']}")
    else:
        print(f"  ✗ 脚本不存在: {skill_info['script']}")
        return None

    # 3. 复制公共模块
    copy_common_module(output_dir)

    # 4. 复制配置工具和环境检查脚本到 scripts 目录
    common_scripts_dir = PROJECT_ROOT / "skills" / COMMON_MODULE / "scripts"
    if common_scripts_dir.exists():
        for script_name in ["bt-config.py", "check_env.py"]:
            script_file = common_scripts_dir / script_name
            if script_file.exists():
                shutil.copy(script_file, scripts_dir / script_name)
                (scripts_dir / script_name).chmod(0o755)
                print(f"  ✓ 复制工具: scripts/{script_name}")

    # 5. 创建配置示例
    create_config_example(output_dir)

    # 6. 创建 README
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
   python3 scripts/{skill_info['script']} --help
   ```

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
    (output_dir / "README.md").write_text(readme_content, encoding="utf-8")
    print(f"  ✓ 创建 README.md")

    return output_dir


def create_archive(skill_dir: Path, dist_dir: Path, format: str = "zip") -> Optional[Path]:
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


def build_all_skills(dist_dir: Path, create_zip: bool = True) -> list:
    """构建所有技能"""
    built_skills = []

    for skill_name in SKILLS:
        skill_dir = build_single_skill(skill_name, dist_dir)
        if skill_dir:
            if create_zip:
                create_archive(skill_dir, dist_dir)
            built_skills.append(skill_name)

    return built_skills


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="宝塔面板日志巡检技能打包工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 打包所有技能
  python3 scripts/build_skills.py

  # 打包单个技能
  python3 scripts/build_skills.py --skill bt-system-monitor

  # 打包并创建 tar.gz 格式
  python3 scripts/build_skills.py --format tar.gz

  # 只构建目录，不创建压缩包
  python3 scripts/build_skills.py --no-zip
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
        default="dist",
        help="输出目录，默认 dist",
    )

    args = parser.parse_args()

    # 输出目录
    dist_dir = PROJECT_ROOT / args.output

    print("=" * 60)
    print("宝塔面板日志巡检技能打包工具")
    print("=" * 60)
    print(f"输出目录: {dist_dir}")
    print(f"压缩格式: {args.format if not args.no_zip else '不压缩'}")

    # 清理输出目录
    clean_dist(dist_dir)

    # 构建
    if args.skill == "all":
        built = build_all_skills(dist_dir, create_zip=not args.no_zip)
    else:
        skill_dir = build_single_skill(args.skill, dist_dir)
        if skill_dir and not args.no_zip:
            create_archive(skill_dir, dist_dir, args.format)
        built = [args.skill] if skill_dir else []

    # 输出结果
    print("\n" + "=" * 60)
    print("构建完成!")
    print("=" * 60)

    # 列出生成的文件
    print("\n生成的文件:")
    for item in sorted(dist_dir.iterdir()):
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
