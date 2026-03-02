# bt-skills

宝塔面板日志巡检技能包 - 符合 OpenClaw/AgentSkills 规范的 Python 实现

## 功能特性

- **系统资源监控** - CPU、内存、磁盘、网络实时监控
- **安全事件巡检** - SSH登录分析、防火墙状态、可疑IP检测
- **服务健康检查** - 网站、数据库、服务状态检测
- **跨平台支持** - 支持 Linux、macOS、Windows

## 目录结构

```
bt-skills/
├── skills/
│   ├── bt_system/               # 公共模块
│   │   ├── __init__.py
│   │   ├── bt_client.py         # 宝塔API客户端
│   │   ├── config.py            # 配置管理
│   │   └── utils.py             # 工具函数
│   │
│   ├── bt-system-monitor/       # 系统资源监控技能
│   │   ├── SKILL.md             # 技能说明
│   │   └── scripts/
│   │       └── monitor.py       # 执行脚本
│   │
│   ├── bt-security-check/       # 安全事件巡检技能
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       └── security.py
│   │
│   └── bt-health-check/         # 服务健康检查技能
│       ├── SKILL.md
│       └── scripts/
│           └── health.py
│
├── scripts/
│   ├── check_env.py             # 环境检查脚本
│   └── build_skills.py          # 技能打包脚本
│
├── config/
│   ├── servers.yaml.example     # 配置示例
│   └── servers.local.yaml       # 本地配置（需自行创建）
│
├── tests/                       # 单元测试
├── dist/                        # 打包输出目录
├── pyproject.toml               # 项目配置
├── requirements.txt             # 依赖列表
└── README.md
```

## 快速开始

### 1. 环境检查

首次使用前，运行环境检查脚本确认环境就绪：

```bash
# 检查环境（人类可读格式）
python3 scripts/check_env.py

# JSON 格式输出（供 AI 解析）
python3 scripts/check_env.py --format json

# 静默模式（只输出状态）
python3 scripts/check_env.py --quiet
```

输出示例：
```
============================================================
宝塔面板日志巡检技能包 - 环境检查
============================================================

🖥️  操作系统: Linux (x86_64)
🐍 Python: 3.13.5
   状态: ✅ Python 版本符合要求

📦 依赖检查:
   ✅ requests: 2.32.3
   ✅ pyyaml: 6.0.2
   ✅ rich: 13.7.0

⚙️  配置检查:
   ✅ 配置文件已就绪

📁 技能目录:
   ✅ bt_common
   ✅ bt-system-monitor
   ✅ bt-security-check
   ✅ bt-health-check

============================================================
✅ 环境检查通过，可以开始使用!
============================================================
```

### 2. 安装依赖

**Linux (Debian/Ubuntu):**
```bash
sudo apt install python3 python3-pip python3-yaml python3-requests
pip3 install rich --user
```

**Linux (CentOS/RHEL):**
```bash
sudo dnf install python3 python3-pip python3-pyyaml python3-requests
pip3 install rich --user
```

**macOS:**
```bash
brew install python3 pyyaml
pip3 install requests rich
```

**Windows:**
```powershell
pip install requests pyyaml rich
```

或使用 pip 统一安装：
```bash
pip install -r requirements.txt
```

### 3. 配置服务器

复制配置模板并填入实际的宝塔面板信息：

```bash
cp config/servers.yaml.example config/servers.local.yaml
```

编辑 `config/servers.local.yaml`：

```yaml
servers:
  - name: "prod-01"
    host: "https://your-panel.com:8888"
    token: "YOUR_API_TOKEN"
    timeout: 10000
    enabled: true

  - name: "prod-02"
    host: "https://your-panel-2.com:8888"
    token: "YOUR_API_TOKEN"
    timeout: 10000
    enabled: true

global:
  retryCount: 3
  retryDelay: 1000
  concurrency: 3
  thresholds:
    cpu: 80      # CPU使用率告警阈值(%)
    memory: 85   # 内存使用率告警阈值(%)
    disk: 90     # 磁盘使用率告警阈值(%)
```

### 4. 获取宝塔API Token

1. 登录宝塔面板
2. 进入 **面板设置** -> **API接口**
3. 开启API接口
4. 复制API密钥（Token）

## 使用方法

### 命令行使用

每个技能脚本都可以独立运行：

```bash
# 系统资源监控
python3 skills/bt-system-monitor/scripts/monitor.py --help
python3 skills/bt-system-monitor/scripts/monitor.py --server prod-01
python3 skills/bt-system-monitor/scripts/monitor.py --format table

# 安全事件巡检
python3 skills/bt-security-check/scripts/security.py --help
python3 skills/bt-security-check/scripts/security.py --server prod-01
python3 skills/bt-security-check/scripts/security.py --output security-report.json

# 服务健康检查
python3 skills/bt-health-check/scripts/health.py --help
python3 skills/bt-health-check/scripts/health.py --check-services
python3 skills/bt-health-check/scripts/health.py --format table
```

### 通用参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--server`, `-s` | 指定服务器名称 | 所有服务器 |
| `--format`, `-f` | 输出格式 (json/table) | json |
| `--output`, `-o` | 输出文件路径 | 标准输出 |
| `--config`, `-c` | 配置文件路径 | 自动查找 |

### 环境变量

可以通过环境变量指定配置文件路径：

```bash
export BT_CONFIG_PATH=/path/to/servers.local.yaml
python3 skills/bt-system-monitor/scripts/monitor.py
```

## 技能打包

使用打包脚本将技能打包为独立可用的压缩包：

```bash
# 打包所有技能
python3 scripts/build_skills.py

# 打包单个技能
python3 scripts/build_skills.py --skill bt-system-monitor

# 打包并创建 tar.gz 格式
python3 scripts/build_skills.py --format tar.gz

# 只构建目录，不创建压缩包
python3 scripts/build_skills.py --no-zip

# 指定输出目录
python3 scripts/build_skills.py --output ./release
```

打包后的文件结构：

```
dist/
├── bt-system-monitor/          # 系统监控技能目录
├── bt-system-monitor.zip       # 系统监控技能压缩包
├── bt-security-check/          # 安全巡检技能目录
├── bt-security-check.zip       # 安全巡检技能压缩包
├── bt-health-check/            # 健康检查技能目录
├── bt-health-check.zip         # 健康检查技能压缩包
├── bt-skills-all/              # 综合包目录
└── bt-skills-all.zip           # 综合包压缩包
```

每个独立技能包都可以单独部署使用：

```bash
# 解压后即可使用
unzip bt-system-monitor.zip
cd bt-system-monitor
python3 scripts/monitor.py --help
```

## 与 OpenClaw 集成

### 技能规范

每个技能目录包含 `SKILL.md` 文件，符合 OpenClaw 技能规范：

```yaml
---
name: bt-system-monitor
description: 系统资源监控技能
user-invocable: true
disable-model-invocation: false
metadata:
  openclaw:
    requires:
      bins:
        - python3
      env:
        - BT_CONFIG_PATH
    primaryEnv: BT_CONFIG_PATH
---
```

### 安装到 OpenClaw

```bash
# 复制技能目录到 OpenClaw 技能目录
cp -r skills/* ~/.openclaw/skills/

# 重启 OpenClaw 会话
```

### Python API 使用

```python
from bt_common import BtClientManager

# 初始化客户端管理器
manager = BtClientManager()
manager.load_config("config/servers.local.yaml")

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

## 技能说明

### bt-system-monitor（系统资源监控）

监控服务器的 CPU、内存、磁盘使用情况：

```bash
python3 skills/bt-system-monitor/scripts/monitor.py
```

输出示例：

```json
{
  "timestamp": "2024-01-15T10:30:00",
  "servers": [
    {
      "server": "prod-01",
      "metrics": {
        "cpu": {"usage": 25.3, "cores": 4},
        "memory": {"used": 3.2, "total": 8.0, "percent": 40.0},
        "disk": {"used": 35.8, "total": 100.0, "percent": 35.8}
      },
      "alerts": []
    }
  ],
  "summary": {"total": 1, "healthy": 1, "warning": 0, "critical": 0}
}
```

### bt-security-check（安全事件巡检）

检查 SSH 配置、防火墙状态、登录日志：

```bash
python3 skills/bt-security-check/scripts/security.py
```

检查项目：
- SSH 端口是否为默认端口
- 是否允许密码登录
- 是否允许 root 登录
- 防火墙是否启用
- 检测暴力破解攻击

### bt-health-check（服务健康检查）

检查网站、数据库、服务运行状态：

```bash
python3 skills/bt-health-check/scripts/health.py
```

检查项目：
- Nginx/Apache 等 Web 服务
- MySQL/MariaDB 数据库服务
- Redis/Memcached 缓存服务
- PHP-FPM 运行状态
- SSL 证书有效期

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
