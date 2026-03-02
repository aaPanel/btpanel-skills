---
name: bt-security-check
description: 安全事件巡检技能，检查SSH登录、防火墙状态、可疑活动等
user-invocable: true
disable-model-invocation: false
metadata:
  openclaw:
    requires:
      bins:
        - python3
---

# 宝塔面板安全巡检

检查宝塔面板服务器的安全状态，包括SSH配置、防火墙状态、登录日志等。

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
```

## 用法

```bash
# 检查所有服务器安全状态
python3 {baseDir}/bt-security-check/scripts/security.py

# 检查指定服务器
python3 {baseDir}/bt-security-check/scripts/security.py --server prod-01

# JSON格式输出
python3 {baseDir}/bt-security-check/scripts/security.py --format json

# 表格格式输出
python3 {baseDir}/bt-security-check/scripts/security.py --format table

# 输出到文件
python3 {baseDir}/bt-security-check/scripts/security.py --output security-report.json

# 指定配置文件
python3 {baseDir}/bt-security-check/scripts/security.py --config /path/to/config.yaml
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--server`, `-s` | 指定服务器名称 | 所有服务器 |
| `--format`, `-f` | 输出格式 (json/table) | json |
| `--output`, `-o` | 输出文件路径 | 标准输出 |
| `--config`, `-c` | 配置文件路径 | 自动查找 |

## 检查项目

### SSH 安全
- SSH 端口配置（默认端口22告警）
- 密码登录状态
- Root 登录权限

### 防火墙
- 防火墙运行状态
- 规则数量统计

### 登录日志
- 失败登录统计
- 可疑 IP 识别
- 暴力破解检测

## 输出示例

```json
{
  "timestamp": "2024-01-15T10:30:00",
  "servers": [
    {
      "server": "prod-01",
      "ssh": {
        "port": 22,
        "status": "running",
        "analysis": {
          "status": "warning",
          "issues": [
            {"level": "warning", "message": "SSH使用默认端口22"}
          ]
        }
      },
      "firewall": {
        "status": "running",
        "enabled": true
      },
      "riskLevel": "medium",
      "alerts": []
    }
  ],
  "summary": {"total": 1, "low": 0, "medium": 1, "high": 0, "critical": 0}
}
```

## 风险等级

| 等级 | 说明 |
|------|------|
| **low** | 无安全问题 |
| **medium** | 1-2个警告级问题 |
| **high** | 3+个警告或1个严重问题 |
| **critical** | 存在严重安全风险 |

## 故障排除

### 常见问题

**1. 无法获取 SSH 信息**
```
原因: 宝塔面板 API 权限不足
解决: 确保面板 API 接口已开启并具有安全模块权限
```

**2. 防火墙状态未知**
```
原因: 某些系统可能不支持防火墙状态获取
解决: 手动检查防火墙状态
```

**3. 宝塔版本不兼容**
```
注意: 请确保宝塔面板版本 >= 9.0
```

## 独立部署

此技能可以独立部署，使用打包脚本：

```bash
python3 {baseDir}/scripts/build_skills.py --skill bt-security-check
```

打包后的技能位于 `dist/bt-security-check/` 目录。
