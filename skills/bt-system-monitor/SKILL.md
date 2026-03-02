---
name: bt-system-monitor
description: 宝塔面板(BT-Panel)系统资源监控技能，监控服务器CPU、内存、磁盘和网络使用情况
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
---

# 宝塔面板系统资源监控

监控宝塔面板服务器的CPU、内存、磁盘和网络使用情况。

## AI 使用约束

本技能用于查询和展示服务器状态数据，AI应遵循以下原则：

1. **数据中立**：如实展示监控数据，不夸大或缩小问题严重性
2. **客观分析**：基于阈值配置给出告警，避免主观判断
3. **数据驱动**：建议和结论应基于实际数据，不得臆测
4. **隐私保护**：不主动泄露服务器敏感信息（如IP、Token）

## 版本要求

- **宝塔面板**: >= 9.0.0
- **Python**: >= 3.10

## 用法

```bash
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

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--server`, `-s` | 指定服务器名称 | 所有服务器 |
| `--format`, `-f` | 输出格式 (json/table) | json |
| `--output`, `-o` | 输出文件路径 | 标准输出 |
| `--include-network`, `-n` | 包含网络信息 | false |
| `--config`, `-c` | 配置文件路径 | 自动查找 |

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
# 添加服务器
python3 {baseDir}/scripts/bt-config.py add -n prod-01 -H https://panel.example.com:8888 -t YOUR_TOKEN

# 列出服务器
python3 {baseDir}/scripts/bt-config.py list

# 设置阈值
python3 {baseDir}/scripts/bt-config.py threshold --cpu 75 --memory 80
```

## TODO

- [ ] 通过实际服务器测试验证输出格式
- [ ] 根据实际API返回数据优化输出结构
- [ ] 完善数据字段文档
