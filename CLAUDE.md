# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

宝塔面板(BT-Panel)运维监控技能包，符合 OpenClaw/AgentSkills 规范的 Python 实现。

**版本要求**: 宝塔面板 >= 9.0.0, Python >= 3.10

## 常用命令

```bash
# 运行测试
python3 -m pytest tests/ -v
python3 -m pytest tests/test_bt_client.py -v  # 运行单个测试文件

# 代码格式化和检查
ruff format .
ruff check .

# 打包技能
python3 scripts/build_skills.py                  # 打包所有技能
python3 scripts/build_skills.py --skill btpanel  # 打包单个技能
python3 scripts/build_skills.py --no-zip         # 只构建目录，不压缩

# 配置管理
python3 src/btpanel/scripts/bt-config.py init    # 初始化配置
python3 src/btpanel/scripts/bt-config.py list    # 列出服务器
python3 src/btpanel/scripts/bt-config.py add -n prod-01 -H https://panel.example.com:8888 -t TOKEN

# 监控脚本（开发时）
python3 src/btpanel/scripts/monitor.py --help
python3 src/btpanel/scripts/sites.py --help
python3 src/btpanel/scripts/services.py --help
python3 src/btpanel/scripts/logs.py --help
python3 src/btpanel/scripts/ssh.py --help
python3 src/btpanel/scripts/crontab.py --help
```

## 架构

```
src/                        # 源码目录（开发时使用）
├── bt_common/              # 公共模块
│   ├── __init__.py         # 模块导出
│   ├── api_endpoints.py    # 宝塔API端点定义、服务常量
│   ├── bt_client.py        # 宝塔API客户端 + BtClientManager多服务器管理
│   ├── config.py           # 配置管理（支持多配置源）
│   ├── utils.py            # 工具函数（格式化、阈值检查、网站解析）
│   └── scripts/
│       ├── bt-config.py    # 配置管理CLI
│       └── check_env.py    # 环境检查
│
└── btpanel/                # 宝塔面板技能
    ├── SKILL.md            # 技能说明（OpenClaw规范）
    └── scripts/
        ├── monitor.py      # 系统资源监控
        ├── sites.py        # 网站状态检查
        ├── services.py     # 服务状态检查
        ├── logs.py         # 日志读取
        ├── ssh.py          # SSH状态和日志
        ├── crontab.py      # 计划任务检查
        └── bt-config.py    # 配置管理工具

skills/                     # 打包输出目录
├── btpanel/                # 打包后的技能（可直接部署）
└── btpanel.zip             # 技能压缩包
```

## 关键设计

### 双环境导入兼容

技能脚本需要同时支持开发环境和打包后的发布环境：

```python
_skill_root = Path(__file__).parent.parent
if (_skill_root / "bt_common").exists():
    sys.path.insert(0, str(_skill_root))          # 发布环境: scripts/ -> bt_common/
else:
    sys.path.insert(0, str(_skill_root.parent / "src"))  # 开发环境: src/bt_common/
```

### 配置优先级

1. `BT_CONFIG_PATH` 环境变量
2. 全局配置 `~/.openclaw/bt-skills.yaml`
3. 本地配置 `config/servers.local.yaml`
4. 默认配置 `config/servers.yaml`

### 宝塔API签名

宝塔API使用 MD5 签名：`request_token = md5(time + md5(token))`

### 服务状态字段

| 字段 | 说明 |
|------|------|
| `installed` (setup) | 服务是否已安装，未安装则无法获取日志 |
| `status` | 服务是否正在运行（仅 installed=true 时有意义） |
| `version` | 已安装的版本号 |
| `pid` | 主进程ID |

### PHP多版本共存

PHP是支持多版本共存的服务，服务名称格式：`php-X.X`（如 `php-8.2`、`php-7.4`）

### 支持的日志服务

| 服务 | 日志类型 | 获取方式 |
|------|----------|----------|
| nginx | 错误日志 | 文件读取 |
| apache | 错误日志 | 文件读取 |
| redis | 日志文件 | 文件读取 |
| mysql | 错误日志/慢日志 | API接口 |
| pgsql | 错误日志/慢日志 | 插件API |

## 测试

测试文件位于 `tests/` 目录，使用 pytest。所有API端点、客户端方法、工具函数都有对应测试。

## 打包说明

打包脚本 `scripts/build_skills.py` 会：
1. 从 `src/` 目录复制源码到 `skills/btpanel/`
2. 复制 `icon/` 图标资源
3. 生成 `README.md`
4. 创建 zip 压缩包

打包后的技能可直接部署到 OpenClaw：`cp -r skills/btpanel ~/.openclaw/skills/`
