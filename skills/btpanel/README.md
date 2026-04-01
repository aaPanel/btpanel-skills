# btpanel

宝塔面板技能包，详细使用说明请参考 SKILL.md。

## 依赖

- Python >= 3.10
- requests
- pyyaml

安装依赖：
```bash
pip install requests pyyaml
```

## 快速开始

1. 配置服务器：
```bash
python3 scripts/bt-config.py add -n SERVER_NAME -H https://panel.example.com:8888 -t YOUR_TOKEN
```

2. 运行脚本：
```bash
python3 scripts/bt-config.py --help
```

## 可用脚本

| 脚本 | 说明 |
|------|------|
| bt-config.py | 参见 SKILL.md |
| crontab.py | 参见 SKILL.md |
| logs.py | 参见 SKILL.md |
| monitor.py | 参见 SKILL.md |
| services.py | 参见 SKILL.md |
| sites.py | 参见 SKILL.md |
| ssh.py | 参见 SKILL.md |
| bt-config.py | 服务器配置管理 |
