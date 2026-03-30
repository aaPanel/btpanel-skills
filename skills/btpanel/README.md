# btpanel

宝塔面板(BT-Panel)运维监控技能，提供服务器资源监控、网站状态检查、服务状态检查、SSH安全审计、计划任务管理、日志读取等功能

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
   python3 scripts/bt-config.py add -n prod-01 -H https://panel.example.com:8888 -t TOKEN
   ```

3. 运行:
   ```bash
   python3 scripts/monitor.py --help
   ```

## 可用脚本

| 脚本 | 功能 |
|------|------|
| monitor.py | 系统资源监控 |
| sites.py | 网站状态检查 |
| services.py | 服务状态检查 |
| logs.py | 日志读取 |
| ssh.py | SSH 状态和登录日志 |
| crontab.py | 计划任务检查 |
| bt-config.py | 配置管理工具 |

详细使用说明请参考 SKILL.md
