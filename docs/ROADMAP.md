# 宝塔面板运维助手开发规划

## 概述

本文档规划 bt-skills 运维助手能力的后续开发方向，涵盖服务状态监控、日志分析、网站检查、任务管理等功能。

---

## 一、功能模块总览

| 模块 | 功能 | 优先级 | 对应技能 |
|------|------|--------|----------|
| 服务状态监控 | Nginx/PHP/MySQL/Redis等服务状态 | P0 | bt-health-check |
| 服务日志查看 | 错误日志、访问日志、慢查询日志 | P1 | bt-health-check |
| SSH登录日志 | 登录记录、失败尝试、可疑IP | P0 | bt-security-check |
| 网站状态检查 | 运行状态、SSL到期、域名解析 | P0 | bt-health-check |
| 计划任务检查 | 定时任务列表、执行状态 | P1 | 新增技能/扩展现有 |
| 备份任务检查 | 备份列表、最近备份时间 | P1 | 新增技能/扩展现有 |

---

## 二、模块详细设计

### 2.1 服务状态监控

#### 功能需求
- 检测常用服务的运行状态
- 显示服务版本信息
- 检测服务是否开机自启
- 提供重启/启动/停止建议

#### 服务列表

| 服务 | 检测方式 | 关键指标 |
|------|----------|----------|
| Nginx | systemctl status / 进程检测 | 运行状态、版本、连接数 |
| Apache | systemctl status / 进程检测 | 运行状态、版本 |
| MySQL/MariaDB | systemctl status + API | 运行状态、版本、连接数 |
| PHP-FPM | systemctl status + API | 运行状态、版本、进程数 |
| Redis | systemctl status + API | 运行状态、内存使用 |
| Memcached | systemctl status + API | 运行状态、内存使用 |
| Docker | systemctl status | 运行状态、容器数 |
| Supervisor | systemctl status | 运行状态、进程数 |

#### 宝塔API端点（待确认）
```
# 服务列表
POST /system?action=GetServiceList

# 服务状态
POST /system?action=GetServiceStatus
  参数: name (服务名)

# 服务管理
POST /system?action=ServiceAdmin
  参数: name (服务名), act (start/stop/restart)
```

#### 输出结构
```json
{
  "services": [
    {
      "name": "nginx",
      "display_name": "Nginx",
      "status": "running",
      "enabled": true,
      "version": "1.24.0",
      "uptime": "15天",
      "metrics": {
        "connections": 1250,
        "workers": 4
      }
    }
  ],
  "summary": {
    "total": 5,
    "running": 4,
    "stopped": 1,
    "critical_stopped": ["mysql"]
  },
  "alerts": [
    {"level": "critical", "service": "mysql", "message": "关键服务 MySQL 已停止"}
  ]
}
```

---

### 2.2 服务日志查看

#### 功能需求
- 查看最近 N 条日志
- 按级别过滤（error, warning, info）
- 按时间范围过滤
- 关键字搜索

#### 日志类型

| 日志 | 路径/获取方式 | 关键信息 |
|------|---------------|----------|
| Nginx 错误日志 | /www/wwwlogs/nginx_error.log | 错误时间、级别、描述 |
| Nginx 访问日志 | /www/wwwlogs/域名.log | 访问统计、状态码分布 |
| PHP 错误日志 | /www/server/php/版本/var/log/ | PHP错误、警告 |
| PHP 慢日志 | /www/server/php/版本/var/log/slow.log | 慢请求追踪 |
| MySQL 错误日志 | /www/server/mysql/var/ | 数据库错误 |
| MySQL 慢查询日志 | /www/server/mysql/var/mysql-slow.log | 慢查询SQL |

#### 宝塔API端点（待确认）
```
# 获取错误日志
POST /site?action=GetErrorLog
  参数: siteName (网站名)

# 获取站点日志
POST /site?action=GetSiteLogs
  参数: siteName (网站名)

# 获取PHP日志（可能需要文件读取）
```

#### 输出结构
```json
{
  "log_type": "nginx_error",
  "server": "prod-01",
  "total": 156,
  "logs": [
    {
      "time": "2024-01-15 10:30:00",
      "level": "error",
      "message": "connect() failed (111: Connection refused)",
      "source": "upstream",
      "count": 12
    }
  ],
  "summary": {
    "errors": 45,
    "warnings": 23,
    "info": 88
  }
}
```

---

### 2.3 SSH登录日志

#### 功能需求
- 显示最近登录记录
- 统计失败登录尝试
- 识别可疑IP（多次失败）
- 检测暴力破解行为

#### 数据来源
- 宝塔面板安全日志 API
- 系统日志 `/var/log/auth.log` 或 `/var/log/secure`

#### 宝塔API端点（待确认）
```
# 安全日志
POST /safe?action=GetLogs
  参数: page, limit

# SSH信息
POST /safe?action=GetSshInfo
```

#### 输出结构
```json
{
  "server": "prod-01",
  "ssh": {
    "port": 22,
    "status": "running",
    "password_auth": true,
    "root_login": false,
    "issues": [
      {"level": "warning", "message": "SSH使用默认端口22"}
    ]
  },
  "recent_logins": [
    {
      "time": "2024-01-15 10:30:00",
      "user": "root",
      "ip": "192.168.1.100",
      "method": "password",
      "status": "success"
    }
  ],
  "failed_attempts": [
    {
      "ip": "203.0.113.50",
      "count": 156,
      "last_attempt": "2024-01-15 10:25:00",
      "usernames": ["root", "admin", "test"]
    }
  ],
  "suspicious_ips": [
    {
      "ip": "203.0.113.50",
      "reason": "5分钟内失败登录156次",
      "risk": "high"
    }
  ],
  "summary": {
    "total_logins": 45,
    "failed_logins": 156,
    "unique_ips": 12,
    "suspicious_count": 2
  }
}
```

---

### 2.4 网站状态检查

#### 功能需求
- 列出所有网站及运行状态
- 检查SSL证书有效期
- 显示网站基本信息（域名、路径、PHP版本）
- 显示进程信息（Java/Node/Go/Python/.NET项目）
- 识别反向代理和重定向配置

#### 网站类型与API端点

宝塔面板按项目类型分不同API端点获取网站列表：

| 类型 | API端点 | 进程信息 | 备注 |
|------|---------|----------|------|
| PHP | `/datalist/data/get_data_list` | ❌ 无 | Nginx/Apache托管，只有配置状态 |
| Java | `/mod/java/project/project_list` | ✅ `pid_info` | SpringBoot等 |
| Node | `/project/nodejs/get_project_list` | ✅ `load_info` | PM2管理 |
| Go | `/project/go/get_project_list` | ✅ `load_info` | Go程序 |
| Python | `/project/python/GetProjectList` | ✅ `pids`/`run` | Gunicorn等 |
| .NET | `/project/net/get_project_list` | ✅ `load_info` | .NET应用 |

#### PHP项目关键字段

```json
{
  "id": 34,
  "name": "example.com",
  "path": "/www/wwwroot/example",
  "status": "1",              // "1"=运行, "0"=停止
  "stop": "",                 // 非空表示已停止
  "project_type": "PHP",
  "php_version": "8.4",
  "php_version_status": true,
  "ssl": {
    "issuer": "Let's Encrypt",
    "notAfter": "2024-01-29",
    "endtime": -763           // 负数=已过期，天数
  },
  "proxy": false,             // 是否反向代理
  "redirect": false,          // 是否重定向
  "waf": {"status": true},    // 防火墙状态
  "domain": 2,                // 域名数量
  "backup_count": 0,          // 备份数量
  "site_total_status": true,  // 整体状态
  "net": {                    // 流量统计
    "one_day_total_flow": 680,
    "one_day_total_pv": 0
  }
}
```

#### Java/Node/Go/NET项目进程信息

```json
{
  "pid": 3180584,
  "status": "睡眠",           // 进程状态
  "memory_used": 22224896,    // 内存使用(bytes)
  "cpu_percent": 0.0,         // CPU使用率
  "threads": 12,              // 线程数
  "connects": 0,              // 连接数
  "running_time": 0.12,       // 运行时间(小时)
  "exe": "/path/to/executable"
}
```

#### 运行状态判断逻辑

```
PHP项目:
  - status == "1" && stop == "" → 运行中
  - status == "0" || stop != "" → 已停止

Java项目:
  - pid_info存在 && pid > 0 → 运行中
  - starting == true → 启动中

Node项目:
  - load_info存在 && 有pid → 运行中
  - run == true → 运行中

Go/NET项目:
  - load_info存在 && 有pid → 运行中
  - run == true → 运行中

Python项目:
  - run == true → 运行中
  - pids非空 → 运行中
```

#### SSL证书状态判断

```python
def check_ssl_status(ssl_data):
    if ssl_data == -1 or ssl_data is None:
        return {"status": "none", "message": "未配置SSL"}

    endtime = ssl_data.get("endtime", 0)
    if endtime < 0:
        return {"status": "expired", "message": f"已过期{-endtime}天"}
    elif endtime <= 7:
        return {"status": "critical", "message": f"将在{endtime}天内过期"}
    elif endtime <= 30:
        return {"status": "warning", "message": f"将在{endtime}天内过期"}
    else:
        return {"status": "valid", "message": f"剩余{endtime}天"}
```

---

### 2.5 计划任务检查

#### 功能需求
- 列出所有计划任务
- 显示任务执行状态
- 检查最近执行结果
- 统计失败任务

#### 宝塔API端点（待确认）
```
# 计划任务列表
POST /crontab?action=GetCrontabList

# 任务执行日志
POST /crontab?action=GetCrontabLogs
  参数: id (任务ID)
```

#### 输出结构
```json
{
  "tasks": [
    {
      "id": 1,
      "name": "每日备份",
      "type": "backup",
      "schedule": "0 2 * * *",
      "status": "enabled",
      "last_run": "2024-01-15 02:00:00",
      "last_status": "success",
      "last_duration": "45s",
      "next_run": "2024-01-16 02:00:00"
    }
  ],
  "summary": {
    "total": 8,
    "enabled": 7,
    "disabled": 1,
    "failed_recently": 1
  },
  "alerts": [
    {"level": "warning", "task": "日志清理", "message": "最近3次执行失败"}
  ]
}
```

---

### 2.6 备份任务检查

#### 功能需求
- 列出备份配置和执行情况
- 显示最近备份时间
- 检查备份文件大小
- 备份存储空间预警

#### 宝塔API端点（待确认）
```
# 备份列表
POST /data?action=GetDataList
  参数: type (site/database/path)

# 备份设置
POST /backup?action=GetBackupList
```

#### 输出结构
```json
{
  "backups": [
    {
      "type": "site",
      "name": "example.com",
      "enabled": true,
      "schedule": "每日 02:00",
      "retention": 7,
      "last_backup": {
        "time": "2024-01-15 02:00:00",
        "size": "256MB",
        "status": "success",
        "path": "/www/backup/site/example.com/"
      },
      "total_size": "1.8GB",
      "count": 7
    }
  ],
  "storage": {
    "backup_path": "/www/backup",
    "total_size": "50GB",
    "used_size": "35GB",
    "free_size": "15GB",
    "used_percent": 70
  },
  "alerts": [
    {"level": "warning", "message": "备份目录磁盘使用率超过70%"}
  ]
}
```

---

## 三、API端点整理

### 已确认的端点

| 功能 | 端点 | 状态 |
|------|------|------|
| 系统状态 | `/system?action=GetNetWork` | ✅ 已使用 |
| 服务列表 | `/system?action=GetServiceList` | ⏳ 待验证 |
| 网站列表 | `/site?action=GetSiteList` | ⏳ 待验证 |
| 数据库列表 | `/database?action=GetDatabases` | ⏳ 待验证 |
| SSH信息 | `/safe?action=GetSshInfo` | ⏳ 待验证 |
| 防火墙状态 | `/safe?action=GetFirewallStatus` | ⏳ 待验证 |
| 安全日志 | `/safe?action=GetLogs` | ⏳ 待验证 |

### 待确认的端点

| 功能 | 预期端点 | 备注 |
|------|----------|------|
| 服务状态 | `/system?action=GetServiceStatus` | 需验证参数 |
| 服务管理 | `/system?action=ServiceAdmin` | 启停服务 |
| 网站SSL | `/site?action=GetSSL` | 需验证 |
| 网站状态 | `/site?action=GetSiteStatus` | 需验证 |
| 计划任务 | `/crontab?action=GetCrontabList` | 需验证 |
| 备份列表 | `/backup?action=GetBackupList` | 需验证 |
| PHP状态 | `/php?action=GetPHPStatus` | 需验证 |

---

## 四、实现优先级建议

### 第一阶段：核心监控（1-2天）

1. **服务状态监控** - bt-health-check 增强
   - 扩展 API 端点获取服务列表
   - 解析服务运行状态
   - 关键服务停止告警

2. **网站状态检查** - bt-health-check 增强
   - 获取网站列表
   - 检查运行状态
   - SSL 证书到期检查

### 第二阶段：安全增强（1天）

3. **SSH登录日志** - bt-security-check 增强
   - 获取登录日志
   - 失败尝试分析
   - 可疑IP识别

### 第三阶段：运维效率（1-2天）

4. **计划任务检查** - 新增功能
   - 获取任务列表
   - 执行状态检查

5. **备份任务检查** - 新增功能
   - 备份状态检查
   - 存储空间预警

### 第四阶段：日志分析（1天）

6. **服务日志查看** - 新增功能
   - 错误日志摘要
   - 关键日志统计

---

## 五、技术实现要点

### 5.1 API 探测方法

```python
# 使用现有的 bt_client 探测 API
client = BtClient(name="test", host="...", token="...")

# 尝试调用 API 并记录返回
try:
    result = client.request("/system?action=GetServiceList")
    print(json.dumps(result, indent=2, ensure_ascii=False))
except Exception as e:
    print(f"API 调用失败: {e}")
```

### 5.2 数据结构扩展

在 `bt_common/utils.py` 中新增：

```python
def parse_service_list(data: list, server_name: str) -> dict:
    """解析服务列表"""
    pass

def parse_site_list(data: list, server_name: str) -> dict:
    """解析网站列表"""
    pass

def parse_ssh_logs(data: dict, server_name: str) -> dict:
    """解析SSH登录日志"""
    pass
```

### 5.3 新增技能目录

```
skills/
├── bt-health-check/       # 增强健康检查
│   └── scripts/
│       └── health.py       # 现有
│       └── services.py     # 新增：服务状态
│       └── sites.py        # 新增：网站检查
│
├── bt-security-check/     # 增强安全检查
│   └── scripts/
│       └── security.py     # 现有
│       └── ssh_logs.py     # 新增：SSH日志
│
├── bt-task-check/         # 新增：任务检查技能
│   ├── SKILL.md
│   └── scripts/
│       └── tasks.py        # 计划任务
│       └── backups.py      # 备份任务
```

---

## 六、后续行动

1. **API 验证**：使用现有服务器逐一验证上述 API 端点
2. **数据结构确认**：记录实际 API 返回的数据结构
3. **功能开发**：按优先级实现各模块
4. **文档更新**：更新 SKILL.md 和 TODO

---

*文档创建时间: 2024-01-15*
*最后更新: 2024-01-15*
