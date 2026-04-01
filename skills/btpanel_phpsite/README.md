# btpanel_phpsite

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
python3 scripts/database.py --help
```

## 可用脚本

| 脚本 | 说明 |
|------|------|
| database.py | 参见 SKILL.md |
| domain.py | 参见 SKILL.md |
| php.py | 参见 SKILL.md |
| rewrite.py | 参见 SKILL.md |
| site.py | 参见 SKILL.md |
| ssl_cert.py | 参见 SKILL.md |
| bt-config.py | 服务器配置管理 |
