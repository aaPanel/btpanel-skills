# bt-skills

宝塔面板运维监控技能包 - 符合 OpenClaw/AgentSkills 规范的 Python 实现

## 功能特性

- **系统资源监控** - CPU、内存、磁盘、网络、负载实时监控
- **网站状态检查** - 支持 PHP/Java/Node/Go/Python/.NET/Proxy/HTML 等多种项目类型
- **服务状态检查** - Nginx/Apache/Redis/MySQL/PHP 等服务状态检测
- **SSH安全审计** - SSH服务状态、登录日志分析、IP归属地查询
- **计划任务管理** - 定时任务查看、备份任务监控
- **日志读取** - Nginx/Apache/Redis/PostgreSQL 日志读取
- **多服务器管理** - 支持同时管理多台宝塔面板服务器

## 目录结构

```
bt-skills/
├── src/                        # 源码目录（开发时使用）
│   ├── bt_common/              # 公共模块
│   │   ├── __init__.py
│   │   ├── api_endpoints.py    # API端点定义
│   │   ├── bt_client.py        # 宝塔API客户端
│   │   ├── config.py           # 配置管理
│   │   ├── utils.py            # 工具函数
│   │   └── scripts/
│   │       └── bt-config.py    # 配置管理工具
│   │
│   └── btpanel/                # 宝塔面板技能
│       ├── SKILL.md            # 技能说明
│       └── scripts/
│           ├── monitor.py      # 系统资源监控
│           ├── sites.py        # 网站状态检查
│           ├── services.py     # 服务状态检查
│           ├── logs.py         # 日志读取
│           ├── ssh.py          # SSH状态和日志
│           ├── crontab.py      # 计划任务检查
│           └── bt-config.py    # 配置管理工具
│
├── skills/                     # 打包输出目录
│   ├── btpanel/                # 打包后的技能目录
│   └── btpanel.zip             # 技能压缩包
│
├── config/
│   └── servers.yaml            # 配置示例
│
├── tests/                      # 单元测试
├── scripts/
│   └── build_skills.py         # 技能打包脚本
│
├── docs/                       # API文档
├── pyproject.toml              # 项目配置
└── requirements.txt            # 依赖列表
```

## 技能说明

### btpanel（宝塔面板运维监控）

综合运维监控技能，提供服务器资源监控、网站状态检查、服务状态检查、SSH安全审计、计划任务管理、日志读取等功能。

#### 可用脚本

| 脚本 | 功能 |
|------|------|
| monitor.py | 系统资源监控（CPU、内存、磁盘、网络） |
| sites.py | 网站状态检查（运行状态、SSL证书） |
| services.py | 服务状态检查（Nginx、Apache、Redis等） |
| logs.py | 日志读取（Nginx、Apache、Redis、PostgreSQL） |
| ssh.py | SSH状态和登录日志检查 |
| crontab.py | 计划任务和备份任务检查 |
| bt-config.py | 服务器配置管理工具 |

## 快速开始

### 1. 安装依赖

```bash
pip install requests pyyaml rich
```

### 2. 配置服务器

```bash
# 使用配置工具添加服务器
python3 src/btpanel/scripts/bt-config.py add -n prod-01 -H https://panel.example.com:8888 -t YOUR_API_TOKEN

# 查看已配置的服务器
python3 src/btpanel/scripts/bt-config.py list
```

或手动创建配置文件 `~/.openclaw/bt-skills.yaml`:

```yaml
servers:
  - name: "prod-01"
    host: "https://your-panel.com:8888"
    token: "YOUR_API_TOKEN"
    timeout: 10000
    enabled: true

global:
  thresholds:
    cpu: 80      # CPU使用率告警阈值(%)
    memory: 85   # 内存使用率告警阈值(%)
    disk: 90     # 磁盘使用率告警阈值(%)
```

### 3. 获取宝塔API Token

1. 登录宝塔面板
2. 进入 **面板设置** -> **API接口**
3. 开启API接口
4. 复制API密钥（Token）

### 4. 运行监控

```bash
# 查看所有服务器资源状态
python3 src/btpanel/scripts/monitor.py --format table

# 查看指定服务器的网站状态
python3 src/btpanel/scripts/sites.py --server prod-01

# 检查服务状态
python3 src/btpanel/scripts/services.py

# 查看SSH登录日志
python3 src/btpanel/scripts/ssh.py --logs --filter failed

# 查看Nginx错误日志
python3 src/btpanel/scripts/logs.py --service nginx --lines 200
```

## 技能打包

使用打包脚本将技能打包为独立可用的压缩包：

```bash
# 打包技能
python3 scripts/build_skills.py

# 打包指定技能
python3 scripts/build_skills.py --skill btpanel

# 只构建目录，不创建压缩包
python3 scripts/build_skills.py --no-zip

# 创建 tar.gz 格式
python3 scripts/build_skills.py --format tar.gz
```

打包后的文件位于 `skills/` 目录，可直接部署使用。

## 与 OpenClaw 集成

### 技能规范

技能目录包含 `SKILL.md` 文件，符合 OpenClaw 技能规范：

```yaml
---
name: btpanel
description: 宝塔面板(BT-Panel)运维监控技能
user-invocable: true
disable-model-invocation: false
metadata:
  openclaw:
    requires:
      bins:
        - python3
---
```

### 安装到 OpenClaw

**推荐方式（首选）：通过 ClawHub 一键安装**

```bash
clawhub install btpanel
```

**手动方式（本地开发/离线场景）**

```bash
# 复制技能目录到 OpenClaw 技能目录
cp -r skills/btpanel ~/.openclaw/skills/

# 重启 OpenClaw 会话
```

### Python API 使用

```python
from bt_common import BtClientManager

# 初始化客户端管理器
manager = BtClientManager()
manager.load_config()

# 获取服务器列表
print(manager.get_server_list())

# 检查连接状态
connections = manager.check_all_connections()
print(connections)

# 获取特定服务器的系统状态
client = manager.get_client("prod-01")
status = client.get_system_status()
print(status)
```

## 版本要求

- **宝塔面板**: >= 9.0.0
- **Python**: >= 3.10

## 开发

### 运行测试

```bash
python3 -m pytest tests/ -v
```

### 代码风格

```bash
# 格式化代码
ruff format .

# 检查代码
ruff check .
```

## 注意事项

1. **安全存储 Token** - 请勿将包含真实 Token 的配置文件提交到版本控制
2. **HTTPS 证书** - 宝塔面板默认使用自签名证书，本工具已禁用证书验证
3. **API 权限** - 确保宝塔面板 API 接口已开启
4. **网络访问** - 确保运行本工具的服务器能访问宝塔面板

## 许可证

MIT
