# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

宝塔面板(BT-Panel)日志巡检技能包，符合 OpenClaw/AgentSkills 规范的 Python 实现。

**版本要求**: 宝塔面板 >= 9.0.0, Python >= 3.10

## 常用命令

```bash
# 运行测试
python3 -m pytest tests/ -v

# 代码格式化
ruff format .

# 代码检查
ruff check .

# 打包技能
python3 scripts/build_skills.py              # 打包所有技能
python3 scripts/build_skills.py --skill bt-system-monitor  # 打包单个技能
python3 scripts/build_skills.py --no-zip     # 只构建目录，不压缩

# 环境检查
python3 skills/bt_common/scripts/check_env.py

# 配置管理
python3 skills/bt_common/scripts/bt-config.py init
python3 skills/bt_common/scripts/bt-config.py list
```

## 架构

```
skills/
├── bt_common/              # 公共模块（所有技能共享）
│   ├── __init__.py         # 模块导出
│   ├── api_endpoints.py    # 宝塔API端点定义
│   ├── bt_client.py        # 宝塔API客户端 + 多服务器管理
│   ├── config.py           # 配置管理（支持全局配置 ~/.openclaw/bt-skills.yaml）
│   ├── utils.py            # 工具函数
│   └── scripts/            # 公共脚本
│       ├── bt-config.py    # 配置管理CLI
│       └── check_env.py    # 环境检查
│
├── bt-system-monitor/      # 系统资源监控技能
├── bt-security-check/      # 安全事件巡检技能
└── bt-health-check/        # 服务健康检查技能

每个技能目录结构：
{skill}/
├── SKILL.md                # 技能说明（OpenClaw规范）
└── scripts/
    └── {main_script}.py    # 主脚本
```

## 关键设计

### 双环境导入兼容

技能脚本需要同时支持开发环境和打包后的发布环境：

```python
# 开发环境: skills/bt_common/scripts/xxx.py -> skills/bt_common/
# 发布环境: {baseDir}/scripts/xxx.py -> {baseDir}/bt_common/
_script_root = Path(__file__).parent.parent
if (_script_root / "bt_common").exists():
    sys.path.insert(0, str(_script_root))      # 发布环境
elif (_script_root / "skills" / "bt_common").exists():
    sys.path.insert(0, str(_script_root / "skills"))  # 开发环境
```

### 配置优先级

1. `BT_CONFIG_PATH` 环境变量
2. 全局配置 `~/.openclaw/bt-skills.yaml`
3. 本地配置 `config/servers.local.yaml`
4. 默认配置 `config/servers.yaml`

### 宝塔API签名

宝塔API使用 MD5 签名：`request_token = md5(time + md5(token))`

### SKILL.md 中的 {baseDir}

`{baseDir}` 指向技能安装的根目录，路径示例：
- 脚本: `{baseDir}/scripts/monitor.py`
- 配置工具: `{baseDir}/scripts/bt-config.py`

## 测试

测试文件位于 `tests/` 目录，使用 pytest：
```bash
python3 -m pytest tests/ -v           # 运行所有测试
python3 -m pytest tests/test_bt_client.py -v  # 运行单个测试文件
```
