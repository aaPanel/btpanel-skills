---
name: bt-security-check
description: 宝塔面板(BT-Panel)安全事件巡检技能，检查SSH登录、防火墙状态、可疑活动等安全风险
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
      - 安全巡检
      - SSH安全
      - 防火墙
      - 入侵检测
---

# 宝塔面板安全巡检

检查宝塔面板服务器的安全状态，包括SSH配置、防火墙状态、登录日志等。

## AI 使用约束

本技能用于查询和展示服务器安全状态，AI应遵循以下原则：

1. **数据中立**：如实展示安全检测结果，不夸大风险等级
2. **客观分析**：基于检测规则给出风险等级，避免主观判断
3. **数据驱动**：建议和结论应基于实际检测结果，不得臆测
4. **隐私保护**：不主动泄露服务器敏感信息（如IP、Token、密码）
5. **安全建议**：提供标准化的安全建议，避免激进操作建议

## 版本要求

- **宝塔面板**: >= 9.0.0
- **Python**: >= 3.10

## 用法

```bash
# 查看帮助
python3 {baseDir}/scripts/security.py -h
python3 {baseDir}/scripts/bt-config.py -h
python3 {baseDir}/scripts/check_env.py -h

# 检查所有服务器安全状态
python3 {baseDir}/scripts/security.py

# 检查指定服务器
python3 {baseDir}/scripts/security.py --server prod-01

# JSON格式输出
python3 {baseDir}/scripts/security.py --format json

# 表格格式输出
python3 {baseDir}/scripts/security.py --format table

# 输出到文件
python3 {baseDir}/scripts/security.py --output security-report.json
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

## 风险等级

| 等级 | 条件 | 说明 |
|------|------|------|
| low | 无安全问题 | 服务器安全配置良好 |
| medium | 1-2个警告级问题 | 建议优化安全配置 |
| high | 3+个警告或1个严重问题 | 需要尽快处理 |
| critical | 存在严重安全风险 | 需要立即处理 |

## TODO

- [ ] 通过实际服务器测试验证输出格式
- [ ] 根据实际API返回数据优化输出结构
- [ ] 完善数据字段文档
- [ ] 验证登录日志分析逻辑
