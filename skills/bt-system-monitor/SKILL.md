---
name: bt-system-monitor
description: 系统资源监控技能，监控CPU、内存、磁盘和网络使用情况
user-invocable: true
disable-model-invocation: false
metadata:
  openclaw:
    requires:
      bins:
        - python3
---

# 宝塔面板系统资源监控

监控宝塔面板服务器的CPU、内存、磁盘和网络使用情况。

## 版本要求

- **宝塔面板**: >= 9.0.0
- **Python**: >= 3.10

## 环境要求

### 支持平台
- Linux (Ubuntu 20.04+, CentOS 7+, Debian 10+)
- macOS (10.15+)
- Windows 10/11

### Python 版本
- Python 3.10 或更高版本

### 依赖
- `requests>=2.28` - HTTP 请求
- `pyyaml>=6.0` - YAML 配置解析
- `rich>=13.0` - 可选，用于表格输出

## 快速开始

### 1. 环境检查

首次使用前，运行环境检查脚本确认环境就绪：

```bash
# 检查环境
python3 {baseDir}/scripts/check_env.py

# JSON 格式输出（供 AI 解析）
python3 {baseDir}/scripts/check_env.py --format json
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
pip install -r {baseDir}/requirements.txt
```

### 3. 配置服务器

配置文件支持两种位置：

**方式一：全局配置（推荐）**
```bash
# 全局配置路径
~/.openclaw/bt-skills.yaml
```

**方式二：本地配置**
```bash
# 本地配置路径
{baseDir}/config/servers.local.yaml
```

配置文件内容：
```yaml
servers:
  - name: "prod-01"
    host: "https://your-panel.com:8888"
    token: "YOUR_API_TOKEN"
    timeout: 10000
    enabled: true

global:
  thresholds:
    cpu: 80
    memory: 85
    disk: 90
```

### 4. 获取宝塔 API Token

1. 登录宝塔面板（版本 >= 9.0）
2. 进入 **面板设置** -> **API接口**
3. 开启 API 接口
4. 复制 API 密钥（Token）

## 用法

```bash
# 监控所有服务器
python3 {baseDir}/bt-system-monitor/scripts/monitor.py

# 监控指定服务器
python3 {baseDir}/bt-system-monitor/scripts/monitor.py --server prod-01

# JSON格式输出
python3 {baseDir}/bt-system-monitor/scripts/monitor.py --format json

# 表格格式输出
python3 {baseDir}/bt-system-monitor/scripts/monitor.py --format table

# 输出到文件
python3 {baseDir}/bt-system-monitor/scripts/monitor.py --output report.json

# 包含网络信息
python3 {baseDir}/bt-system-monitor/scripts/monitor.py --include-network

# 指定配置文件
python3 {baseDir}/bt-system-monitor/scripts/monitor.py --config /path/to/config.yaml
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--server`, `-s` | 指定服务器名称 | 所有服务器 |
| `--format`, `-f` | 输出格式 (json/table) | json |
| `--output`, `-o` | 输出文件路径 | 标准输出 |
| `--include-network`, `-n` | 包含网络信息 | false |
| `--config`, `-c` | 配置文件路径 | 自动查找 |

## 输出示例

```json
{
  "timestamp": "2024-01-15T10:30:00",
  "servers": [
    {
      "server": "prod-01",
      "metrics": {
        "cpu": {"usage": 45.2, "cores": 4},
        "memory": {"used": 3.5, "total": 8.0, "percent": 43.75},
        "disk": {"used": 50.2, "total": 100.0, "percent": 50.2}
      },
      "alerts": []
    }
  ],
  "summary": {"total": 1, "healthy": 1, "warning": 0, "critical": 0}
}
```

## 告警阈值

可在配置文件中设置告警阈值：

```yaml
global:
  thresholds:
    cpu: 80      # CPU使用率告警阈值(%)
    memory: 85   # 内存使用率告警阈值(%)
    disk: 90     # 磁盘使用率告警阈值(%)
```

## 故障排除

### 常见问题

**1. 配置文件未找到**
```
错误: 未找到配置文件
解决: 创建 ~/.openclaw/bt-skills.yaml 或设置 BT_CONFIG_PATH 环境变量
```

**2. 连接失败**
```
错误: 无法连接到服务器
解决: 检查网络连接、面板地址和 API Token 是否正确
```

**3. 宝塔版本不兼容**
```
注意: 请确保宝塔面板版本 >= 9.0
```

**4. SSL 证书错误**
```
注意: 默认禁用 SSL 证书验证（宝塔面板使用自签名证书）
```

## 独立部署

此技能可以独立部署，使用打包脚本：

```bash
python3 {baseDir}/scripts/build_skills.py --skill bt-system-monitor
```

打包后的技能位于 `dist/bt-system-monitor/` 目录。
