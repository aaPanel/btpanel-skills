# btpanel_files

宝塔面板文件管理技能，提供远程服务器文件/目录浏览、读取、编辑、创建、删除、权限管理等基本文件操作能力

## 版本要求

- **宝塔面板**: >= 9.0.0
- **Python**: >= 3.10

## 快速开始

1. 安装依赖:
   ```bash
   pip install requests pyyaml
   ```

2. 配置服务器:
   ```bash
   # 使用配置工具添加服务器
   python3 scripts/bt-config.py add --name prod-01 --host https://panel.example.com:8888 --token YOUR_TOKEN
   ```

3. 运行:
   ```bash
   # 查看帮助
   python3 scripts/files.py --help

   # 查看目录
   python3 scripts/files.py ls /www
   ```

## 可用命令

| 命令 | 功能 |
|------|------|
| ls | 列出目录内容 |
| cat | 读取文件内容 |
| edit | 编辑文件内容 |
| mkdir | 创建目录 |
| touch | 创建文件 |
| rm | 删除文件 |
| rmdir | 删除目录 |
| stat | 查看文件权限 |
| chmod | 设置文件权限 |

详细使用说明请参考 SKILL.md
