---
name: bt-health-check
description: 宝塔面板(BT-Panel)服务健康检查技能，检查网站、数据库、服务等运行状态
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
      - 健康检查
      - 服务监控
      - 网站状态
      - 数据库状态
---

# 宝塔面板服务健康检查

检查宝塔面板服务器的服务运行状态，包括网站、数据库、系统服务等。

## AI 使用约束

本技能用于查询和展示服务器健康状态，AI应遵循以下原则：

1. **数据中立**：如实展示健康检查结果，不夸大或淡化问题
2. **客观分析**：基于检查规则给出状态判断，避免主观判断
3. **数据驱动**：建议和结论应基于实际检查数据，不得臆测
4. **隐私保护**：不主动泄露服务器敏感信息（如IP、Token、域名）
5. **状态优先级**：critical > warning > healthy，优先报告严重问题

## 版本要求

- **宝塔面板**: >= 9.0.0
- **Python**: >= 3.10

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
- SSL 证书有效期检查
- 网站路径信息

### 数据库状态
- 数据库数量统计
- 数据库大小统计

## 健康状态

| 状态 | 条件 | 说明 |
|------|------|------|
| healthy | 无告警 | 所有服务正常运行 |
| warning | 存在非关键警告 | 需要关注但不紧急 |
| critical | 关键服务停止或SSL即将过期 | 需要立即处理 |

### 关键服务

以下服务停止会触发 critical 告警：

| 服务 | 类型 |
|------|------|
| nginx | Web服务器 |
| apache | Web服务器 |
| mysql | 数据库 |
| mariadb | 数据库 |
| redis | 缓存 |

### SSL 证书告警

| 剩余天数 | 告警级别 |
|----------|----------|
| ≤ 7 天 | critical |
| ≤ 30 天 | warning |

## TODO

- [ ] 通过实际服务器测试验证输出格式
- [ ] 根据实际API返回数据优化输出结构
- [ ] 完善数据字段文档
- [ ] 验证SSL证书检查逻辑