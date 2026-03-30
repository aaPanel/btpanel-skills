# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

宝塔面板 (BT-Panel) 运维监控技能包，符合 OpenClaw/AgentSkills 规范的 Python 实现。

**版本要求**: 宝塔面板 >= 9.0.0, Python >= 3.10

## 常用命令

```bash
# 安装依赖
pip install -e ".[dev]"

# 运行测试
python3 -m pytest tests/ -v
python3 -m pytest tests/test_bt_client.py -v                    # 运行单个测试文件
python3 -m pytest tests/test_bt_client.py::TestHostNormalization -v  # 运行单个测试类

# 代码格式化和检查
ruff format .
ruff check .

# 打包技能
python3 scripts/build_skills.py                      # 打包所有技能
python3 scripts/build_skills.py --skill btpanel      # 打包 btpanel 技能
python3 scripts/build_skills.py --skill btpanel_files  # 打包 btpanel_files 技能
python3 scripts/build_skills.py --no-zip             # 只构建目录，不压缩
python3 scripts/build_skills.py --format tar.gz      # 创建 tar.gz 格式

# 配置管理
python3 src/btpanel/scripts/bt-config.py init    # 初始化配置
python3 src/btpanel/scripts/bt-config.py list    # 列出服务器
python3 src/btpanel/scripts/bt-config.py add -n prod-01 -H 192.168.1.1:8888 -t TOKEN

# 监控脚本（开发时）
python3 src/btpanel/scripts/monitor.py --help
python3 src/btpanel/scripts/sites.py --help
python3 src/btpanel/scripts/services.py --help
python3 src/btpanel/scripts/logs.py --help
python3 src/btpanel/scripts/ssh.py --help
python3 src/btpanel/scripts/crontab.py --help

# 文件操作技能（开发时）
PYTHONPATH=src python3 -m btpanel_files.scripts.files --help
PYTHONPATH=src python3 -m btpanel_files.scripts.files ls /www
PYTHONPATH=src python3 -m btpanel_files.scripts.files cat /www/test.txt
PYTHONPATH=src python3 -m btpanel_files.scripts.files mkdir /www/newdir
PYTHONPATH=src python3 -m btpanel_files.scripts.files chmod 755 /www/test.txt
```

## 架构

```
src/                        # 源码目录（开发时使用）
├── bt_common/              # 公共模块
│   ├── __init__.py         # 模块导出
│   ├── api_endpoints.py    # 宝塔 API 端点定义、服务常量
│   ├── bt_client.py        # 宝塔 API 客户端 + BtClientManager 多服务器管理
│   ├── config.py           # 配置管理、URL 规范化
│   ├── utils.py            # 工具函数（格式化、阈值检查、网站解析）
│   ├── files_client.py     # 文件操作客户端（FilesClient、FilesClientManager）
│   └── scripts/
│       ├── bt-config.py    # 配置管理 CLI
│       └── check_env.py    # 环境检查
│
├── btpanel/                # 宝塔面板技能
│   ├── SKILL.md            # 技能说明（OpenClaw 规范）
│   └── scripts/
│       ├── monitor.py      # 系统资源监控
│       ├── sites.py        # 网站状态检查
│       ├── services.py     # 服务状态检查
│       ├── logs.py         # 日志读取
│       ├── ssh.py          # SSH 状态和日志
│       ├── crontab.py      # 计划任务检查
│       └── bt-config.py    # 配置管理工具
│
└── btpanel_files/          # 宝塔文件操作技能（独立）
    ├── SKILL.md            # 技能说明
    ├── README.md           # 使用说明
    ├── QUICKSTART.md       # 快速入门指南
    └── scripts/
        └── files.py        # CLI 命令实现（调用 bt_common + 格式化输出）

skills/                     # 打包输出目录
├── btpanel/                # 打包后的技能（可直接部署）
└── btpanel.zip             # 技能压缩包
```

### 核心模块职责

- **bt_client.py**: `BtClient` 类封装宝塔 API 请求，`BtClientManager` 管理多服务器连接
- **config.py**: 配置加载、URL 规范化 (`normalize_host`)、服务器增删改
- **utils.py**: 数据格式化 (`format_bytes`, `format_uptime`)、阈值检查、网站/项目解析
- **files_client.py**: 文件操作客户端 (`FilesClient`、`FilesClientManager`)，封装文件/目录管理 API
- **api_endpoints.py**: 定义所有 API 端点常量、支持的 PHP 版本、服务日志路径

## 关键设计

### 双环境导入兼容

技能脚本需要同时支持开发环境和打包后的发布环境：

```python
_script_root = Path(__file__).parent.parent
if (_script_root / "bt_common").exists():
    sys.path.insert(0, str(_script_root))          # 发布环境：scripts/ -> bt_common/
else:
    sys.path.insert(0, str(_script_root.parent / "src"))  # 开发环境：src/bt_common/
```

### 配置优先级

1. `BT_CONFIG_PATH` 环境变量
2. 全局配置 `~/.openclaw/bt-skills.yaml`
3. 本地配置 `config/servers.local.yaml`
4. 默认配置 `config/servers.yaml`

### URL 规范化

添加服务器时自动规范化地址：
- `192.168.1.1:8888` → `https://192.168.1.1:8888`
- `192.168.1.1:8888/soft/plugin` → `https://192.168.1.1:8888`（移除路径）
- `panel.com:8888/` → `https://panel.com:8888`（移除尾部斜杠）

### 宝塔 API 签名

宝塔 API 使用 MD5 签名：`request_token = md5(time + md5(token))`

### 服务状态字段

| 字段 | 说明 |
|------|------|
| `installed` (setup) | 服务是否已安装，未安装则无法获取日志 |
| `status` | 服务是否正在运行（仅 installed=true 时有意义） |
| `version` | 已安装的版本号 |
| `pid` | 主进程 ID |

### PHP 多版本共存

PHP 是支持多版本共存的服务，服务名称格式：`php-X.X`（如 `php-8.2`、`php-7.4`）

### 支持的日志服务

| 服务 | 日志类型 | 获取方式 |
|------|----------|----------|
| nginx | 错误日志 | 文件读取 |
| apache | 错误日志 | 文件读取 |
| redis | 日志文件 | 文件读取 |
| mysql | 错误日志/慢日志 | API 接口 |
| pgsql | 错误日志/慢日志 | 插件 API |

**注意**：只有已安装的服务才能获取日志，尝试获取未安装服务的日志会返回错误。

## 测试

测试文件位于 `tests/` 目录，使用 pytest。测试覆盖：

- API 签名功能 (`TestSignRequest`)
- 客户端初始化和健康检查 (`TestBtClient`)
- 多服务器管理 (`TestBtClientManager`)
- 配置加载和验证 (`TestConfig`)
- 工具函数 (`TestUtils`)
- API 端点定义 (`TestAPIEndpoints`)
- 网站/项目解析 (`TestSiteParsing`)
- 主机地址规范化 (`TestHostNormalization`)
- 服务 API 定义 (`TestServiceAPI`)
- 文件操作客户端 (`TestFilesClient`)
- 文件操作 CLI 参数解析 (`TestCLIParsers`)

**运行测试**:
```bash
python3 -m pytest tests/test_files_client.py -v  # 文件操作测试
```

## 打包说明

打包脚本 `scripts/build_skills.py` 会：
1. 从 `src/` 目录复制源码到 `skills/btpanel/`
2. 复制 `icon/` 图标资源
3. 生成 `README.md`
4. 创建 zip 压缩包

打包后的技能可直接部署到 OpenClaw：`cp -r skills/btpanel ~/.openclaw/skills/`

## AI 使用约束

参考 `src/btpanel/SKILL.md`，AI 应遵循：

1. **数据中立**：如实展示监控数据，不夸大或缩小问题严重性
2. **客观分析**：基于阈值配置给出告警，避免主观判断
3. **数据驱动**：建议和结论应基于实际数据，不得臆测
4. **隐私保护**：不主动泄露服务器敏感信息（如 IP、Token、域名）
5. **执行前告知**：由于接口数据较多，AI 应先向用户简述即将执行的操作步骤，然后再执行命令获取数据
