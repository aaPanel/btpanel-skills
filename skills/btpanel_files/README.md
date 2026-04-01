# btpanel_files 技能包使用说明

## 安装与配置

### 1. 配置服务器

首先使用 `bt-config` 工具配置服务器信息：

```bash
# 添加服务器
python3 -m btpanel.bt_common.scripts.bt-config add -n myserver -H 192.168.1.100:8888 -t YOUR_TOKEN

# 查看已配置的服务器
python3 -m btpanel.bt_common.scripts.bt-config list
```

### 2. 使用文件操作技能

#### 方法一：使用 CLI 命令

```bash
# 查看目录
python3 -m btpanel_files.files ls /www

# 指定服务器
python3 -m btpanel_files.files -s myserver ls /www

# 读取文件
python3 -m btpanel_files.files cat /www/server/panel/runserver.py

# 读取文件最后 50 行
python3 -m btpanel_files.files cat /www/wwwlogs/error.log -n 50

# 编辑文件
python3 -m btpanel_files.files edit /www/test.txt "Hello World"

# 从文件读取内容并保存
python3 -m btpanel_files.files edit /www/test.txt -f ./local_file.txt

# 创建目录
python3 -m btpanel_files.files mkdir /www/newdir

# 创建文件
python3 -m btpanel_files.files touch /www/newfile.txt

# 删除文件（移入回收站）
python3 -m btpanel_files.files rm /www/test.txt

# 删除目录（移入回收站）
python3 -m btpanel_files.files rmdir /www/olddir

# 查看文件权限
python3 -m btpanel_files.files stat /www/test.txt

# 修改文件权限
python3 -m btpanel_files.files chmod 755 /www/test.txt
python3 -m btpanel_files.files chmod 755 /www/test.txt -u www -R
```

#### 方法二：在 Python 代码中使用

```python
from btpanel_files.files_client import FilesClient

# 创建客户端（使用默认服务器）
client = FilesClient()

# 或者指定服务器
client = FilesClient("myserver")

# 查看目录
result = client.get_dir("/www")
for d in result.get('dir', []):
    print(f"目录：{d['nm']}")
for f in result.get('files', []):
    print(f"文件：{f['nm']}")

# 读取文件
result = client.get_file_body("/www/test.txt")
print(result['data'])

# 保存文件
result = client.save_file_body("/www/test.txt", "Hello World", "utf-8")
print(result['msg'])

# 创建目录
client.create_dir("/www/newdir")

# 创建文件
client.create_file("/www/newfile.txt")

# 删除文件
client.delete_file("/www/test.txt")

# 删除目录
client.delete_dir("/www/olddir")

# 查看权限
result = client.get_file_access("/www/test.txt")
print(f"权限：{result['chmod']}, 所有者：{result['chown']}")

# 设置权限
client.set_file_access("/www/test.txt", "755", user="www", all_files=True)
```

#### 方法三：便捷方法

```python
from btpanel_files.files_client import FilesClient

client = FilesClient()

# 读取文件内容（直接返回字符串）
content = client.read_file("/www/test.txt")
print(content)

# 写入文件
success = client.write_file("/www/test.txt", "New Content")

# 列出目录（返回格式化的字典）
result = client.list_dir("/www")
for d in result['directories']:
    print(f"📁 {d['nm']}")
for f in result['files']:
    print(f"📄 {f['nm']}")
```

## API 接口说明

### GetDirNew - 获取目录信息

```
GET /files?action=GetDirNew&path={path}&p={page}&showRow={rows}
```

**参数**:
- `path`: 目录路径（URL 编码）
- `p`: 页码（默认 1）
- `showRow`: 每页显示数量（默认 500）

**响应**:
```json
{
  "dir": [{"nm": "目录名", "sz": 大小，"mt": 时间戳，"acc": "权限", "user": "所有者"}],
  "files": [{"nm": "文件名", "sz": 大小，"mt": 时间戳，"acc": "权限", "user": "所有者"}],
  "path": "/www"
}
```

### GetFileBody - 读取文件内容

```
GET /files?action=GetFileBody&path={path}
```

**参数**:
- `path`: 文件路径（URL 编码）

**响应**:
```json
{
  "status": true,
  "only_read": false,
  "size": 639,
  "encoding": "utf-8",
  "data": "文件内容",
  "st_mtime": "1753161154"
}
```

### SaveFileBody - 保存文件内容

```
POST /files?action=SaveFileBody&path={path}&data={data}&encoding={encoding}&st_mtime={mtime}
```

**参数**:
- `path`: 文件路径（URL 编码）
- `data`: 文件内容（URL 编码）
- `encoding`: 文件编码（默认 utf-8）
- `st_mtime`: 文件修改时间戳（用于并发检测）

**响应**:
```json
{
  "status": true,
  "msg": "文件已保存!",
  "historys": ["1774837569"],
  "st_mtime": "1774837569"
}
```

### CreateDir - 创建目录

```
POST /files?action=CreateDir&path={path}
```

### CreateFile - 创建文件

```
POST /files?action=CreateFile&path={path}
```

### DeleteDir - 删除目录

```
POST /files?action=DeleteDir&path={path}
```

### DeleteFile - 删除文件

```
POST /files?action=DeleteFile&path={path}
```

### GetFileAccess - 获取文件权限

```
GET /files?action=GetFileAccess&filename={filename}
```

**响应**:
```json
{"chmod": 755, "chown": "www"}
```

### SetFileAccess - 设置文件权限

```
POST /files?action=SetFileAccess&filename={filename}&access={access}&user={user}&all={all}
```

## 注意事项

1. **路径编码**: 所有路径参数会自动进行 URL 编码，无需手动处理
2. **删除操作**: 删除文件/目录会移动到回收站，非永久删除
3. **并发保护**: 保存文件时会自动检查文件是否被修改，如需强制保存使用 `force=1`
4. **权限要求**: 需要对目标路径有相应的读写权限
5. **文件大小**: 大于 3MB 的文件在线编辑会受到限制

## 故障排查

### 无法连接服务器

```bash
# 检查服务器配置
python3 -m btpanel.bt_common.scripts.bt-config list

# 测试连接
python3 -c "from btpanel_files.files_client import FilesClient; c = FilesClient(); print(c.get_dir('/'))"
```

### 权限不足

确保配置的 API Token 有足够的文件操作权限，在宝塔面板中检查：
- 面板设置 → API 管理 → 检查 Token 权限

### 路径不存在

确保路径是绝对路径，如 `/www/test.txt` 而不是 `test.txt`

## 更新日志

### v1.0.0 (2026-03-30)
- 初始版本发布
- 支持基本的文件/目录操作
- 支持权限管理
- 支持 CLI 和 Python API 两种使用方式
