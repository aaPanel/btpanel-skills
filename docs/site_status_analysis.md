# 网站状态API数据结构分析

## 一、API端点汇总

| 项目类型 | API端点 | 请求参数 |
|----------|---------|----------|
| PHP网站 | `/datalist/data/get_data_list` | `type=-1&search=&p=1&limit=10&table=sites&order=` |
| Java项目 | `/mod/java/project/project_list` | `data={"search":"","p":1,"limit":10,"type_id":""}` |
| Node.js项目 | `/project/nodejs/get_project_list` | `data={"search":"","p":1,"limit":10,"type_id":""}` |
| Go项目 | `/project/go/get_project_list` | `data={"search":"","p":1,"limit":10,"type_id":""}` |
| Python项目 | `/project/python/GetProjectList` | `data={"search":"","p":1,"limit":10,"type_id":""}` |
| .NET项目 | `/project/net/get_project_list` | `search=&p=1&limit=10&type_id=&table=sites` |

## 二、项目类型区分

### 2.1 PHP网站（含静态、反代）

**特点**：
- 只通过Nginx/Apache提供服务
- **没有进程信息**，只有Web服务器配置
- `status` 字段表示配置是否启用（"1"=启用）
- `stop` 字段表示是否被暂停

**关键字段**：
```json
{
  "id": 34,
  "name": "154.mywp.com",
  "path": "/www/wwwroot/11_wp",
  "status": "1",           // 配置状态：1=启用
  "stop": "",              // 暂停标记：空=正常，非空=暂停
  "project_type": "PHP",
  "php_version": "8.4",
  "php_version_status": true,
  "proxy": false,          // 是否反代
  "redirect": false,       // 是否重定向
  "ssl": {                 // SSL证书信息
    "issuer": "Let's Encrypt",
    "notAfter": "2024-01-29",
    "endtime": -763        // 剩余天数，负数=已过期
  },
  "domain": 1,             // 域名数量
  "backup_count": 0,       // 备份数量
  "waf": {"status": true}, // WAF状态
  "net": {                 // 流量统计
    "one_day_total_flow": 680,
    "one_day_total_pv": 0
  },
  "site_total_status": true
}
```

### 2.2 Java项目（SpringBoot等）

**特点**：
- 有进程信息（`pid_info`）
- 有运行状态（`run`字段）
- 支持域名绑定（通过Nginx反向代理）

**关键字段**：
```json
{
  "id": 44,
  "name": "hello-java",
  "path": "/www/wwwroot/dd/JAVA/hello-java.jar",
  "status": "1",
  "project_type": "Java",
  "project_config": {
    "project_jdk": "/www/server/java/jdk1.8.0_371",
    "project_jar": "/www/wwwroot/dd/JAVA/hello-java.jar",
    "java_type": "springboot",
    "port": "",
    "domains": [],
    "bind_extranet": false
  },
  "pid": "3180584",        // 主进程PID
  "pid_info": {
    "pid": 3180584,
    "status": "睡眠",       // 进程状态
    "memory_used": 22224896,
    "cpu_percent": 0.0,
    "threads": 12,
    "connections": [],
    "connects": 0,
    "running_time": 0.12
  },
  "run": true,             // 是否运行中
  "starting": true,        // 是否启动中
  "ssl": {...}
}
```

### 2.3 Node.js项目

**特点**：
- 使用PM2管理进程
- 有进程负载信息（`load_info`）
- 支持集群模式

**关键字段**：
```json
{
  "id": 10,
  "name": "ChanCMS",
  "path": "/www/wwwroot/ChanCMS",
  "project_type": "Node",
  "project_config": {
    "pm2_name": "ChanCMS",
    "cluster": 1,
    "project_type": "pm2",
    "nodejs_version": "v22.21.1",
    "port": 3000,
    "domains": ["aaaa.node.test.com:80"],
    "bind_extranet": 1
  },
  "load_info": {
    "3315441": {
      "name": "node /www/wwwro",
      "pid": 3315441,
      "status": "睡眠",
      "memory_used": 38191104,
      "cpu_percent": 0.14,
      "threads": 11,
      "connects": 2,
      "exe": "node /www/wwwroot/ChanCMS/app.js"
    }
  },
  "run": true,
  "listen_ok": true
}
```

### 2.4 Go项目

**特点**：
- 有进程信息
- 通常单进程运行

**关键字段**：
```json
{
  "id": 17,
  "name": "main_go",
  "path": "/www/wwwroot/111go/main",
  "project_type": "Go",
  "project_config": {
    "project_exe": "/www/wwwroot/111go/main",
    "port": 4433,
    "domains": ["h3h3.hasfgfg.com:80"],
    "bind_extranet": 1
  },
  "load_info": {
    "1991992": {
      "name": "main",
      "pid": 1991992,
      "status": "睡眠",
      "memory_used": 659456,
      "cpu_percent": 0.0,
      "threads": 7,
      "connections": [...],
      "connects": 1
    }
  },
  "run": true
}
```

### 2.5 Python项目

**特点**：
- 支持多种框架（Flask、Django等）
- 使用Gunicorn/uWSGI运行
- 可能有多个进程

**关键字段**：
```json
{
  "id": 45,
  "name": "PYTHON",
  "path": "/www/wwwroot/dd/PYTHON",
  "status": 0,              // 注意：0表示停止
  "project_type": "Python",
  "project_config": {
    "framework": "flask",
    "version": "Python 3.12.11",
    "python_bin": "/www/server/pyporject_evn/versions/3.12.11/bin/python3.12",
    "port": "",
    "processes": 4,
    "threads": 2
  },
  "run": false,
  "pids": []
}
```

### 2.6 .NET项目

**特点**：
- 有进程信息
- 可能有多个关联进程

**关键字段**：
```json
{
  "id": 19,
  "name": "dds",
  "path": "/www/wwwroot/dd/NET/MyWebApi",
  "project_type": "net",
  "project_config": {
    "dotnet_version": "8.0.100",
    "port": 10100,
    "domains": ["testnet.com:80"],
    "bind_extranet": 1
  },
  "load_info": {
    "2029798": {...},  // 启动脚本进程
    "2029799": {...}   // dotnet主进程
  },
  "run": true
}
```

## 三、状态判断逻辑

### 3.1 PHP网站状态

```python
def get_php_site_status(site):
    """PHP网站状态判断"""
    if site.get("stop") and site["stop"] != "":
        return "stopped"     # 已暂停

    if site.get("status") == "1":
        return "running"     # 运行中

    return "disabled"        # 已禁用
```

### 3.2 其他项目状态

```python
def get_project_status(project):
    """其他项目状态判断（Java/Node/Go/Python/.NET）"""
    if project.get("run") is True:
        return "running"     # 运行中

    if project.get("starting") is True:
        return "starting"    # 启动中

    if project.get("status") == "1":
        return "stopped"     # 已停止

    return "disabled"        # 已禁用
```

### 3.3 SSL证书状态

```python
def get_ssl_status(ssl_info):
    """SSL证书状态"""
    if ssl_info == -1 or ssl_info is None:
        return {"enabled": False}

    endtime = ssl_info.get("endtime", 0)

    if endtime < 0:
        return {
            "enabled": True,
            "status": "expired",
            "days_remaining": endtime,
            "issuer": ssl_info.get("issuer_O", "Unknown"),
            "not_after": ssl_info.get("notAfter")
        }
    elif endtime <= 7:
        return {
            "enabled": True,
            "status": "critical",
            "days_remaining": endtime
        }
    elif endtime <= 30:
        return {
            "enabled": True,
            "status": "warning",
            "days_remaining": endtime
        }
    else:
        return {
            "enabled": True,
            "status": "valid",
            "days_remaining": endtime
        }
```

## 四、统一输出结构

```json
{
  "sites": [
    {
      "id": 34,
      "name": "example.com",
      "type": "PHP",
      "status": "running",
      "path": "/www/wwwroot/example",

      // 运行时信息（非PHP项目）
      "runtime": {
        "running": true,
        "pid": 12345,
        "memory_mb": 38.2,
        "cpu_percent": 0.14,
        "threads": 11,
        "connections": 2,
        "uptime": "2天3小时"
      },

      // 技术栈信息
      "stack": {
        "php_version": "8.4",
        "node_version": null,
        "java_version": null,
        "python_version": null,
        "go_version": null,
        "dotnet_version": null
      },

      // 网络配置
      "network": {
        "domains": ["example.com", "www.example.com"],
        "port": 80,
        "ssl": {
          "enabled": true,
          "status": "valid",
          "issuer": "Let's Encrypt",
          "days_remaining": 90,
          "not_after": "2024-04-15"
        },
        "proxy": false,
        "waf_enabled": true
      },

      // 流量统计
      "traffic": {
        "daily_pv": 1000,
        "daily_uv": 500,
        "daily_flow_mb": 680
      }
    }
  ],

  "summary": {
    "total": 10,
    "by_type": {
      "PHP": 4,
      "Java": 2,
      "Node": 2,
      "Go": 1,
      "Python": 1,
      "Net": 0
    },
    "by_status": {
      "running": 8,
      "stopped": 1,
      "disabled": 1
    },
    "ssl": {
      "enabled": 7,
      "expiring_soon": 2,
      "expired": 1
    }
  },

  "alerts": [
    {"level": "critical", "site": "old.com", "message": "SSL证书已过期763天"},
    {"level": "warning", "site": "test.com", "message": "SSL证书将在7天内过期"},
    {"level": "warning", "site": "PYTHON", "message": "项目已停止"}
  ]
}
```

## 五、关键字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `project_type` | string | 项目类型：PHP/Java/Node/Go/Python/net |
| `status` | string/number | 配置状态："1"=启用，其他=禁用 |
| `stop` | string | 暂停标记：空=正常，非空=暂停 |
| `run` | boolean | 进程运行状态（非PHP项目） |
| `pid` / `pids` | string/array | 进程ID |
| `load_info` | object | 进程负载信息 |
| `pid_info` | object | Java项目进程信息 |
| `ssl.endtime` | number | SSL剩余天数，负数=已过期 |
| `bind_extranet` | number | 是否绑定外网：0=否，1=是 |
| `domains` | array | 绑定的域名列表 |
| `proxy` | boolean | 是否反代（PHP项目） |

## 六、注意事项

1. **PHP网站没有进程信息**：只有Nginx/Apache配置，需要通过其他方式判断实际运行状态
2. **状态字段含义不同**：
   - `status`: 配置是否启用
   - `run`: 进程是否运行
   - `stop`: 是否被手动暂停
3. **SSL检测**：`endtime`为负数表示证书已过期天数
4. **多进程项目**：Java/Node/Go/Python/.NET可能有多个进程，`load_info`是字典格式
