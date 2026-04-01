#!/usr/bin/env python3
# /// script
# dependencies = []
# ///
"""
技能打包脚本
将技能打包为独立可用的压缩包，包含公共模块

自动扫描 src 目录下的技能，无需手动定义
"""

import argparse
import shutil
import sys
from pathlib import Path


# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 源码目录
SRC_DIR = PROJECT_ROOT / "src"

# 输出目录
OUTPUT_DIR = PROJECT_ROOT / "skills"

# 公共模块
COMMON_MODULE = "bt_common"

# 排除的目录（不是技能）
EXCLUDE_DIRS = {COMMON_MODULE, "__pycache__"}


def discover_skills() -> dict:
    """自动扫描技能目录"""
    skills = {}
    
    if not SRC_DIR.exists():
        return skills
    
    for item in SRC_DIR.iterdir():
        if not item.is_dir():
            continue
        if item.name in EXCLUDE_DIRS:
            continue
        if item.name.startswith(".") or item.name.startswith("_"):
            continue
        
        # 检查是否有 SKILL.md
        skill_md = item / "SKILL.md"
        if not skill_md.exists():
            print(f"  ⚠ 跳过 {item.name}：缺少 SKILL.md")
            continue
        
        # 检查是否有 scripts 目录
        scripts_dir = item / "scripts"
        if not scripts_dir.exists():
            print(f"  ⚠ 跳过 {item.name}：缺少 scripts 目录")
            continue
        
        # 自动获取脚本列表
        scripts = [s.name for s in scripts_dir.glob("*.py") if not s.name.startswith("_")]
        
        skills[item.name] = {
            "name": item.name,
            "scripts": scripts,
            "src_dir": item,
        }
    
    return skills


def clean_output_dir(output_dir: Path, skill_name: str):
    """清理指定技能的输出目录"""
    skill_output = output_dir / skill_name
    if skill_output.exists():
        shutil.rmtree(skill_output)
    skill_output.mkdir(parents=True, exist_ok=True)
    print(f"  ✓ 清理并创建输出目录")


def copy_common_module(target_dir: Path):
    """复制公共模块到目标目录"""
    common_src = SRC_DIR / COMMON_MODULE
    common_dst = target_dir / COMMON_MODULE

    if common_dst.exists():
        shutil.rmtree(common_dst)

    if not common_src.exists():
        print(f"  ✗ 公共模块源目录不存在: {common_src}")
        return False

    shutil.copytree(common_src, common_dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"))
    print(f"  ✓ 复制公共模块: {COMMON_MODULE}/")
    return True


def copy_icons(target_dir: Path):
    """复制图标资源到目标目录"""
    icons_src = PROJECT_ROOT / "icon"
    icons_dst = target_dir / "icon"

    if not icons_src.exists():
        return

    if icons_dst.exists():
        shutil.rmtree(icons_dst)

    shutil.copytree(icons_src, icons_dst)
    icon_files = list(icons_dst.glob("*"))
    print(f"  ✓ 复制图标资源: icon/ ({len(icon_files)} 个文件)")


def copy_scripts(scripts_dir_src: Path, scripts_dir_dst: Path) -> int:
    """复制 scripts 目录下的所有脚本"""
    if not scripts_dir_src.exists():
        return 0
    
    scripts_dir_dst.mkdir(exist_ok=True)
    
    copied = 0
    for script in scripts_dir_src.glob("*.py"):
        if script.name.startswith("_"):
            continue
        script_dst = scripts_dir_dst / script.name
        shutil.copy(script, script_dst)
        script_dst.chmod(0o755)
        copied += 1
    
    print(f"  ✓ 复制脚本: scripts/ ({copied} 个文件)")
    return copied


def create_simple_readme(skill_name: str, scripts: list, target_dir: Path):
    """创建简单的 README"""
    main_script = scripts[0] if scripts else "main.py"
    
    readme_content = f"""# {skill_name}

宝塔面板技能包，详细使用说明请参考 SKILL.md。

## 依赖

- Python >= 3.10
- requests
- pyyaml

安装依赖：
```bash
pip install requests pyyaml
```

## 快速开始

1. 配置服务器：
```bash
python3 scripts/bt-config.py add -n SERVER_NAME -H https://panel.example.com:8888 -t YOUR_TOKEN
```

2. 运行脚本：
```bash
python3 scripts/{main_script} --help
```

## 可用脚本

| 脚本 | 说明 |
|------|------|
"""
    
    for script in scripts:
        readme_content += f"| {script} | 参见 SKILL.md |\n"
    
    readme_content += f"| bt-config.py | 服务器配置管理 |\n"
    
    (target_dir / "README.md").write_text(readme_content, encoding="utf-8")
    print(f"  ✓ 创建 README.md")


def build_single_skill(skill_info: dict, output_dir: Path, create_zip: bool = True, zip_format: str = "zip") -> Path:
    """构建单个技能包"""
    skill_name = skill_info["name"]
    skill_src_dir = skill_info["src_dir"]
    
    print(f"\n构建技能: {skill_name}")
    
    # 清理并创建输出目录
    clean_output_dir(output_dir, skill_name)
    skill_output_dir = output_dir / skill_name
    
    # 1. 复制 SKILL.md
    skill_md = skill_src_dir / "SKILL.md"
    if skill_md.exists():
        shutil.copy(skill_md, skill_output_dir / "SKILL.md")
        print(f"  ✓ 复制 SKILL.md")
    
    # 2. 复制 README.md（如果有）
    readme_src = skill_src_dir / "README.md"
    if readme_src.exists():
        shutil.copy(readme_src, skill_output_dir / "README.md")
        print(f"  ✓ 复制 README.md")
    
    # 3. 复制 scripts 目录
    scripts_src = skill_src_dir / "scripts"
    scripts_dst = skill_output_dir / "scripts"
    scripts = skill_info.get("scripts", [])
    copy_scripts(scripts_src, scripts_dst)
    
    # 3b. 复制公共脚本
    common_scripts_src = SRC_DIR / COMMON_MODULE / "scripts"
    if common_scripts_src.exists():
        for script in common_scripts_src.glob("*.py"):
            if script.name.startswith("_"):
                continue
            script_dst = scripts_dst / script.name
            shutil.copy(script, script_dst)
            script_dst.chmod(0o755)
        print(f"  ✓ 复制公共脚本: bt_common/scripts/")
    
    # 4. 复制公共模块
    copy_common_module(skill_output_dir)
    
    # 5. 复制图标资源
    copy_icons(skill_output_dir)
    
    # 6. 如果没有 README.md，创建简单的
    if not (skill_output_dir / "README.md").exists():
        create_simple_readme(skill_name, scripts, skill_output_dir)
    
    # 7. 创建压缩包
    if create_zip:
        return create_archive(skill_output_dir, output_dir, zip_format)
    
    return skill_output_dir


def create_archive(skill_dir: Path, output_dir: Path, format: str = "zip") -> Path:
    """创建压缩包"""
    if format == "zip":
        archive_path = shutil.make_archive(
            str(skill_dir),
            "zip",
            skill_dir.parent,
            skill_dir.name,
        )
    elif format == "tar.gz":
        archive_path = shutil.make_archive(
            str(skill_dir),
            "gztar",
            skill_dir.parent,
            skill_dir.name,
        )
    else:
        print(f"  ✗ 不支持的格式: {format}")
        return skill_dir
    
    print(f"  ✓ 创建压缩包: {Path(archive_path).name}")
    return Path(archive_path)


def build_all_skills(output_dir: Path, create_zip: bool = True, zip_format: str = "zip") -> list:
    """构建所有技能"""
    skills = discover_skills()
    
    if not skills:
        print("✗ 未发现任何技能")
        return []
    
    print(f"发现 {len(skills)} 个技能: {', '.join(skills.keys())}")
    
    built = []
    for skill_name, skill_info in skills.items():
        try:
            build_single_skill(skill_info, output_dir, create_zip, zip_format)
            built.append(skill_name)
        except Exception as e:
            print(f"  ✗ 构建失败: {e}")
    
    return built


def main():
    parser = argparse.ArgumentParser(
        description="宝塔面板技能打包工具（自动扫描技能目录）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 scripts/build_skills.py              # 打包所有技能
  python3 scripts/build_skills.py -s btpanel   # 打包单个技能
  python3 scripts/build_skills.py --no-zip     # 只构建目录，不压缩
        """,
    )

    parser.add_argument(
        "--skill", "-s",
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
        help="输出目录，默认 skills/",
    )

    args = parser.parse_args()

    output_dir = Path(args.output) if args.output else OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 50)
    print("宝塔面板技能打包工具")
    print("=" * 50)
    print(f"源码目录: {SRC_DIR}")
    print(f"输出目录: {output_dir}")

    # 发现技能
    skills = discover_skills()
    
    if not skills:
        print("✗ 未发现任何技能")
        return 1
    
    # 构建
    if args.skill == "all":
        built = build_all_skills(output_dir, create_zip=not args.no_zip, zip_format=args.format)
    elif args.skill in skills:
        build_single_skill(skills[args.skill], output_dir, create_zip=not args.no_zip, zip_format=args.format)
        built = [args.skill]
    else:
        print(f"✗ 未知的技能: {args.skill}")
        print(f"  可用技能: {', '.join(skills.keys())}")
        return 1

    # 输出结果
    print("\n" + "=" * 50)
    print("构建完成!")
    print("=" * 50)
    
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