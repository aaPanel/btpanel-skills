---
name: bt-system-monitor
description: 宝塔面板(BT-Panel)系统资源监控技能，监控服务器CPU、内存、磁盘、网络使用情况，以及网站状态检查
user-invocable: true
disable-model-invocation: false
metadata:
  openclaw:
    requires:
      bins:
        - python3
    keywords:
      - 宝塔面板
      - BT-Panel
      - 面板
      - 服务器监控
      - 系统资源
      - CPU监控
      - 内存监控
      - 磁盘监控
      - 网站状态
      - SSL证书
---

# 宝塔面板系统资源监控

监控宝塔面板服务器的CPU、内存、磁盘、网络使用情况，以及网站状态检查。

## AI 使用约束

本技能用于查询和展示服务器状态数据，AI应遵循以下原则：

1. **数据中立**：如实展示监控数据，不夸大或缩小问题严重性
2. **客观分析**：基于阈值配置给出告警，避免主观判断
3. **数据驱动**：建议和结论应基于实际数据，不得臆测
4. **隐私保护**：不主动泄露服务器敏感信息（如IP、Token、域名）

## 版本要求

- **宝塔面板**: >= 9.0.0
- **Python**: >= 3.10

## 用法

### 系统资源监控

```bash
# 查看帮助
python3 {baseDir}/scripts/monitor.py -h

# 监控所有服务器
python3 {baseDir}/scripts/monitor.py

# 监控指定服务器
python3 {baseDir}/scripts/monitor.py --server prod-01

# JSON格式输出
python3 {baseDir}/scripts/monitor.py --format json

# 表格格式输出
python3 {baseDir}/scripts/monitor.py --format table

# 输出到文件
python3 {baseDir}/scripts/monitor.py --output report.json
```

### 网站状态检查

```bash
# 查看帮助
python3 {baseDir}/scripts/sites.py -h

# 检查所有服务器的网站状态
python3 {baseDir}/scripts/sites.py

# 检查指定服务器
python3 {baseDir}/scripts/sites.py --server prod-01

# 只显示停止的网站
python3 {baseDir}/scripts/sites.py --filter stopped

# 只显示SSL即将过期的网站（30天内）
python3 {baseDir}/scripts/sites.py --filter ssl-warning

# 只显示SSL已过期的网站
python3 {baseDir}/scripts/sites.py --filter ssl-expired

# JSON格式输出
python3 {baseDir}/scripts/sites.py --format json

# 输出到文件
python3 {baseDir}/scripts/sites.py --output sites.json
```

## 参数说明

### monitor.py 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--server`, `-s` | 指定服务器名称 | 所有服务器 |
| `--format`, `-f` | 输出格式 (json/table) | json |
| `--output`, `-o` | 输出文件路径 | 标准输出 |
| `--config`, `-c` | 配置文件路径 | 自动查找 |

### sites.py 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--server`, `-s` | 指定服务器名称 | 所有服务器 |
| `--format`, `-f` | 输出格式 (json/table) | table |
| `--output`, `-o` | 输出文件路径 | 标准输出 |
| `--filter` | 过滤条件 (stopped/ssl-warning/ssl-expired) | 无 |
| `--config`, `-c` | 配置文件路径 | 自动查找 |

## 监控指标

### 系统资源监控 (monitor.py)

通过单一API接口获取完整的系统监控数据：

- **CPU**: 使用率、核心数、型号、用户/系统占用
- **内存**: 总量、使用量、可用量、缓存、使用率
- **磁盘**: 多分区详情、总量、使用量、使用率
- **网络**: 实时速度、总流量、各网卡统计
- **负载**: 1/5/15分钟负载
- **系统**: 主机名、操作系统、运行时间、面板版本
- **资源**: 网站、数据库、FTP账户数量

### 网站状态检查 (sites.py)

支持多种项目类型：

| 类型 | 进程信息 | 运行状态判断 |
|------|----------|--------------|
| PHP | 无 | status==1 && stop为空 |
| Java | pid_info | pid > 0 |
| Node | load_info | run==true |
| Go | load_info | run==true |
| Python | pids | run==true |
| .NET | load_info | run==true |

检查项目：
- **运行状态**: 运行中/已停止/启动中
- **SSL证书**: 有效/即将过期/已过期
- **进程信息**: PID、内存、CPU、线程数（适用于Java/Node/Go等）
- **基础信息**: 路径、域名、PHP版本、端口

## SSL证书告警

| 剩余天数 | 告警级别 |
|----------|----------|
| 已过期 | critical |
| ≤ 7 天 | critical |
| ≤ 30 天 | warning |

## 告警阈值

可在配置文件中设置告警阈值：

```yaml
global:
  thresholds:
    cpu: 80      # CPU使用率告警阈值(%)
    memory: 85   # 内存使用率告警阈值(%)
    disk: 90     # 磁盘使用率告警阈值(%)
```

## 配置管理

使用配置工具管理服务器：

```bash
# 查看帮助
python3 {baseDir}/scripts/bt-config.py -h

# 添加服务器
python3 {baseDir}/scripts/bt-config.py add -n prod-01 -H https://panel.example.com:8888 -t YOUR_TOKEN

# 列出服务器
python3 {baseDir}/scripts/bt-config.py list

# 设置阈值
python3 {baseDir}/scripts/bt-config.py threshold --cpu 75 --memory 80
```

## TODO

- [ ] 服务状态检查（Nginx/PHP/MySQL等）
- [ ] SSH登录日志分析
- [ ] 计划任务检查
- [ ] 备份任务检查
