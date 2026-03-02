---
name: bt-health-check
description: 服务健康检查技能，检查网站、数据库、服务等运行状态
user-invocable: true
disable-model-invocation: false
metadata:
  openclaw:
    requires:
      bins:
        - python3
---

# 宝塔面板服务健康检查

检查宝塔面板服务器的服务运行状态，包括网站、数据库、系统服务等。

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
# 检查所有服务器健康状态
python3 {baseDir}/bt-health-check/scripts/health.py

# 检查指定服务器
python3 {baseDir}/bt-health-check/scripts/health.py --server prod-01

# 只检查服务
python3 {baseDir}/bt-health-check/scripts/health.py --check-services

# 只检查网站
python3 {baseDir}/bt-health-check/scripts/health.py --check-sites

# 只检查数据库
python3 {baseDir}/bt-health-check/scripts/health.py --check-databases

# JSON格式输出
python3 {baseDir}/bt-health-check/scripts/health.py --format json

# 表格格式输出
python3 {baseDir}/bt-health-check/scripts/health.py --format table

# 输出到文件
python3 {baseDir}/bt-health-check/scripts/health.py --output health-report.json

# 指定配置文件
python3 {baseDir}/bt-health-check/scripts/health.py --config /path/to/config.yaml
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--server`, `-s` | 指定服务器名称 | 所有服务器 |
| `--format`, `-f` | 输出格式 (json/table) | json |
| `--output`, `-o` | 输出文件路径 | 标准输出 |
| `--check-services` | 只检查服务状态 | 默认全部检查 |
| `--check-sites` | 只检查网站状态 | 默认全部检查 |
| `--check-databases` | 只检查数据库状态 | 默认全部检查 |
| `--config`, `-c` | 配置文件路径 | 自动查找 |

## 检查项目

### 服务状态
- Nginx/Apache 等 Web 服务
- MySQL/MariaDB 数据库服务
- Redis/Memcached 缓存服务
- PHP-FPM 运行状态
- Docker 容器服务
- Supervisor 进程管理

### 网站状态
- 网站运行状态
- SSL 证书有效期检查（7天内告警、30天内警告）
- 网站路径信息

### 数据库状态
- 数据库数量统计
- 数据库大小统计

## 输出示例

```json
{
  "timestamp": "2024-01-15T10:30:00",
  "servers": [
    {
      "server": "prod-01",
      "services": {
        "total": 5,
        "running": 4,
        "stopped": 1
      },
      "sites": {
        "total": 10,
        "running": 10,
        "stopped": 0
      },
      "databases": {
        "total": 3,
        "sizeTotal": 1024.5
      },
      "overallStatus": "warning",
      "alerts": [
        {"level": "critical", "type": "service", "message": "关键服务 redis 已停止"}
      ]
    }
  ],
  "summary": {"total": 1, "healthy": 0, "warning": 1, "critical": 0}
}
```

## 健康状态

| 状态 | 说明 |
|------|------|
| **healthy** | 所有服务正常 |
| **warning** | 存在非关键警告 |
| **critical** | 存在关键服务停止或 SSL 证书即将过期 |

### 关键服务

以下服务停止会触发 critical 告警：
- nginx
- apache
- mysql
- mariadb
- redis

### SSL 证书告警

| 剩余天数 | 告警级别 |
|----------|----------|
| ≤ 7 天 | critical |
| ≤ 30 天 | warning |

## 故障排除

### 常见问题

**1. 服务列表为空**
```
原因: 宝塔面板 API 版本差异
解决: 确保面板版本 >= 9.0
```

**2. 网站状态获取失败**
```
原因: 网站模块 API 权限不足
解决: 检查 API Token 权限
```

**3. 数据库大小显示为 0**
```
原因: 宝塔面板未计算数据库大小
解决: 在面板中手动刷新数据库统计
```

**4. 宝塔版本不兼容**
```
注意: 请确保宝塔面板版本 >= 9.0
```

## 独立部署

此技能可以独立部署，使用打包脚本：

```bash
python3 {baseDir}/scripts/build_skills.py --skill bt-health-check
```

打包后的技能位于 `dist/bt-health-check/` 目录。
