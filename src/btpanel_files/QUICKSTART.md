# btpanel_files 快速入门

## 1. 配置服务器

首先配置宝塔服务器信息：

```bash
# 添加服务器配置
python3 src/btpanel/scripts/bt-config.py add -n test -H "http://192.168.1.100:8888" -t "YOUR_API_TOKEN"

# 查看配置
python3 src/btpanel/scripts/bt-config.py list
```

## 2. 使用文件操作

### 查看目录

```bash
# 查看 /www 目录
PYTHONPATH=src python3 -m btpanel_files.scripts.files ls /www

# 查看指定服务器
PYTHONPATH=src python3 -m btpanel_files.scripts.files -s test ls /www/server
```

### 读取文件

```bash
# 读取文件内容
PYTHONPATH=src python3 -m btpanel_files.scripts.files cat /www/server/panel/runserver.py

# 读取最后 50 行
PYTHONPATH=src python3 -m btpanel_files.scripts.files cat /www/wwwlogs/error.log -n 50
```

### 编辑文件

```bash
# 直接写入内容
PYTHONPATH=src python3 -m btpanel_files.scripts.files edit /www/test.txt "Hello World"

# 从文件读取内容
PYTHONPATH=src python3 -m btpanel_files.scripts.files edit /www/test.txt -f ./local.txt
```

### 管理目录

```bash
# 创建目录
PYTHONPATH=src python3 -m btpanel_files.scripts.files mkdir /www/newdir

# 删除目录（移入回收站）
PYTHONPATH=src python3 -m btpanel_files.scripts.files rmdir /www/olddir
```

### 管理文件

```bash
# 创建文件
PYTHONPATH=src python3 -m btpanel_files.scripts.files touch /www/test.txt

# 删除文件（移入回收站）
PYTHONPATH=src python3 -m btpanel_files.scripts.files rm /www/test.txt
```

### 权限管理

```bash
# 查看权限
PYTHONPATH=src python3 -m btpanel_files.scripts.files stat /www/test.txt

# 修改权限
PYTHONPATH=src python3 -m btpanel_files.scripts.files chmod 755 /www/test.txt

# 递归修改权限
PYTHONPATH=src python3 -m btpanel_files.scripts.files chmod 755 /www/wwwroot -u www -R
```

## 3. 在 Python 代码中使用

```python
import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from btpanel_files.files_client import FilesClient

# 创建客户端
client = FilesClient("test")  # 使用配置的服务器

# 列出目录
result = client.list_dir("/www")
print("=== 目录 ===")
for d in result['directories']:
    print(f"📁 {d['nm']}  {d['acc']}  {d['user']}")

print("=== 文件 ===")
for f in result['files']:
    print(f"📄 {f['nm']}  {f['sz']}B  {f['acc']}")

# 读取文件
content = client.read_file("/www/test.txt")
print(f"文件内容：{content}")

# 写入文件
success = client.write_file("/www/test.txt", "New Content")
print(f"保存成功：{success}")

# 设置权限
client.set_file_access("/www/test.txt", "644", user="www")
```

## 4. 运行测试

```bash
# 运行所有测试
python3 -m pytest tests/test_files_client.py -v

# 测试结果示例：
# 9 passed in 0.35s
```

## 5. 常见问题

### Q: 找不到模块？
A: 确保设置了 `PYTHONPATH=src`

### Q: 连接失败？
A: 检查服务器配置和 API Token 是否正确

### Q: 权限不足？
A: 确保 API Token 有文件操作权限

### Q: 路径不存在？
A: 使用绝对路径，如 `/www/test.txt`

## 6. 命令速查

| 命令 | 说明 | 示例 |
|------|------|------|
| `ls` | 列出目录 | `ls /www` |
| `cat` | 读取文件 | `cat /www/test.txt` |
| `edit` | 编辑文件 | `edit /www/test.txt "content"` |
| `mkdir` | 创建目录 | `mkdir /www/newdir` |
| `touch` | 创建文件 | `touch /www/test.txt` |
| `rm` | 删除文件 | `rm /www/test.txt` |
| `rmdir` | 删除目录 | `rmdir /www/olddir` |
| `stat` | 查看权限 | `stat /www/test.txt` |
| `chmod` | 设置权限 | `chmod 755 /www/test.txt` |

---

**版本**: 1.0.0
**更新**: 2026-03-30
