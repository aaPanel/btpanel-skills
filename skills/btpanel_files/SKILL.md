---
name: btpanel_files
description: 宝塔面板文件管理技能，提供远程服务器文件/目录浏览、读取、编辑、创建、删除、权限管理等基本文件操作能力
user-invocable: true
disable-model-invocation: false
icon: icon/bt.png
metadata:
  openclaw:
    requires:
      bins:
        - python3
    keywords:
      - 宝塔面板
      - BT-Panel
      - 文件管理
      - 文件操作
      - 目录浏览
      - 文件读取
      - 文件编辑
      - 权限管理
---

# 宝塔面板文件管理

宝塔面板服务器文件操作工具，提供远程文件/目录浏览、读取、编辑、创建、删除、权限管理等基本文件操作能力。

![宝塔面板](icon/bt-logo.svg)

## 图标资源

技能包提供以下图标文件，可在生成报告时引用：

| 文件 | 格式 | 用途 |
|------|------|------|
| `icon/bt-logo.svg` | SVG | 矢量图标，适合缩放 |

## AI 使用约束

本技能用于查询和修改服务器文件，AI 应遵循以下原则：

1. **操作前确认**：修改文件前先读取文件内容，确认修改范围
2. **执行前告知**：文件操作会影响服务器状态，AI 应先向用户简述即将执行的操作步骤
3. **谨慎删除**：删除文件/目录前需告知用户，并确认目标路径
4. **隐私保护**：不主动读取敏感文件（如 `/etc/shadow`、`.env`、`config.php` 等含密码的文件）
5. **备份建议**：修改重要配置文件前，建议用户先备份

**执行流程示例**：
```
AI: 我将为您执行以下操作：
    1. 读取配置文件 /www/server/nginx/conf/nginx.conf
    2. 修改指定配置项
    3. 保存文件
    正在获取数据，请稍候...
    [执行命令]
    [展示结果和修改内容]
```

## 宝塔面板相关技能矩阵

当前宝塔面板技能包，共包含 3 个相互关联的技能：

| 技能名称                | 描述 | 依赖关系                              |
|---------------------|------|-----------------------------------|
| **btpanel**         | 运维监控技能 | ✅ 基础技能，主要用于资源监控、网站状态检查、服务状态检查等    |
| **btpanel-files**   | 文件管理技能 | ✅ 提供远程服务器文件辅助服务，可以读取文件列表和内容       |
| **btpanel-phpsite** | PHP 网站管理技能 | ✅ 提供远程服务器 PHP 网站管理功能，能够部署和管理php网站 |



### ⚠️ 常见问题

**问题 1: 配置文件不存在**
```
错误：未找到配置文件
解决：运行 python3 bt-config.py add 添加服务器配置
```

**问题 2: PYTHONPATH 未设置**
```bash
# 运行脚本前需要设置
export PYTHONPATH=/path/to/btpanel-skills/src:$PYTHONPATH
```

### 检查命令

```bash
# 检查 bt_common 模块
python3 -c "from bt_common.bt_client import BtClient; print('✅ 模块正常')"

# 检查配置文件
ls -la ~/.openclaw/bt-skills.yaml

# 测试连接
python3 {baseDir}/scripts/monitor.py --server "你的服务器名"
```

---

## 服务器配置管理

> **重要:** 没有服务器信息时需要先添加

本技能复用 `btpanel` 技能的配置系统，使用 `bt-config.py` 工具管理服务器：

```bash
# 查看帮助
python3 {baseDir}/scripts/bt-config.py -h

# 添加服务器
python3 {baseDir}/scripts/bt-config.py add -n prod-01 -H https://panel.example.com:8888 -t YOUR_TOKEN

# 列出服务器
python3 {baseDir}/scripts/bt-config.py list

# 删除服务器
python3 {baseDir}/scripts/bt-config.py remove prod-01
```

**获取 API Token 的方法**：
1. 登录宝塔面板
2. 进入「面板设置」->「API 接口」
3. 点击「获取 API Token」

**重要提示 - SSL 证书验证配置**：
添加服务器时，AI 应询问用户：
> "您的宝塔面板是否使用了受信任的 SSL 证书（如 Let's Encrypt、商业 CA 证书）？"

- ✅ **是**（受信任证书）→ 使用默认配置，无需额外参数
- ⚠️ **否**（自签名证书）→ 添加 `--verify-ssl false` 参数

**示例**：
```bash
# 自签名证书场景
python3 {baseDir}/scripts/bt-config.py add -n prod-01 -H https://panel.example.com:8888 -t YOUR_TOKEN --verify-ssl false

# 受信任证书场景（默认）
python3 {baseDir}/scripts/bt-config.py add -n prod-01 -H https://panel.example.com:8888 -t YOUR_TOKEN
```

## 常用场景

### 场景一：查看目录文件列表

当用户需要查看服务器某个目录的内容时：

```bash
# 查看/www 目录
python3 {baseDir}/scripts/files.py ls /www

# 查看指定目录
python3 {baseDir}/scripts/files.py ls /www/server/nginx/conf

# 带分页查看
python3 {baseDir}/scripts/files.py ls /www/wwwlogs -p 2 -r 100
```

**用户意图识别**：
- "看看/www 目录下有什么" → 执行 `files.py ls /www`
- "查看 Nginx 配置文件目录" → 执行 `files.py ls /www/server/nginx/conf`
- "这个目录有哪些文件" → 执行 `files.py ls 路径`

### 场景二：读取文件内容

当用户需要查看文件内容时：

```bash
# 读取文件
python3 {baseDir}/scripts/files.py cat /www/test.txt

# 读取文件最后 50 行
python3 {baseDir}/scripts/files.py cat /www/logs/error.log -n 50

# 读取并显示文件信息
python3 {baseDir}/scripts/files.py cat /www/server/nginx/conf/nginx.conf -v
```

**用户意图识别**：
- "帮我看看这个文件内容" → 执行 `files.py cat 路径`
- "查看日志最后几行" → 执行 `files.py cat 路径 -n 50`
- "这个文件是什么编码" → 执行 `files.py cat 路径 -v`

### 场景三：编辑文件内容

当用户需要修改文件内容时：

```bash
# 直接修改文件内容
python3 {baseDir}/scripts/files.py edit /www/test.txt "新内容"

# 从本地文件读取内容并保存
python3 {baseDir}/scripts/files.py edit /www/test.txt -f ./local-file.txt
```

**用户意图识别**：
- "修改这个文件，加上 XXX" → 先读取文件，再执行 `files.py edit`
- "更新配置文件" → 先读取文件，确认后执行 `files.py edit`

**重要**：编辑文件前必须先读取原内容，确认修改范围后再保存。

### 场景四：创建目录/文件

当用户需要创建新目录或文件时：

```bash
# 创建目录
python3 {baseDir}/scripts/files.py mkdir /www/newdir

# 创建文件
python3 {baseDir}/scripts/files.py touch /www/test.txt
```

**用户意图识别**：
- "新建一个目录" → 执行 `files.py mkdir 路径`
- "创建一个空文件" → 执行 `files.py touch 路径`

### 场景五：删除文件/目录

当用户需要删除文件或目录时：

```bash
# 删除文件
python3 {baseDir}/scripts/files.py rm /www/test.txt

# 删除目录
python3 {baseDir}/scripts/files.py rmdir /www/olddir
```

**用户意图识别**：
- "删除这个文件" → 确认路径后执行 `files.py rm 路径`
- "清理这个目录" → 确认路径后执行 `files.py rmdir 路径`

**重要**：删除操作会将文件/目录移动到回收站，非永久删除。但操作前仍需用户确认。

### 场景六：查看/修改文件权限

当用户需要管理文件权限时：

```bash
# 查看文件权限
python3 {baseDir}/scripts/files.py stat /www/test.txt

# 修改文件权限
python3 {baseDir}/scripts/files.py chmod 755 /www/test.txt

# 修改权限并设置所有者
python3 {baseDir}/scripts/files.py chmod 755 /www/test.txt -u www -g www

# 递归修改目录权限
python3 {baseDir}/scripts/files.py chmod 755 /www/wwwroot -R
```

**用户意图识别**：
- "查看这个文件的权限" → 执行 `files.py stat 路径`
- "修改文件权限为 755" → 执行 `files.py chmod 755 路径`
- "把这个目录权限改对" → 确认正确权限后执行 `files.py chmod`

## 版本要求

- **宝塔面板**: >= 9.0.0
- **Python**: >= 3.10

## 用法

### 查看目录列表

```bash
# 查看帮助
python3 {baseDir}/scripts/files.py -h

# 列出目录内容
python3 {baseDir}/scripts/files.py ls /www

# 指定页码和每页数量
python3 {baseDir}/scripts/files.py ls /www/wwwlogs -p 2 -r 100

# 指定服务器
python3 {baseDir}/scripts/files.py ls /www --server prod-01
```

### 读取文件

```bash
# 读取文件内容
python3 {baseDir}/scripts/files.py cat /www/test.txt

# 读取文件最后 N 行
python3 {baseDir}/scripts/files.py cat /www/logs/error.log -n 100

# 读取并显示详细信息
python3 {baseDir}/scripts/files.py cat /www/test.txt -v
```

### 编辑文件

```bash
# 直接指定内容
python3 {baseDir}/scripts/files.py edit /www/test.txt "Hello World"

# 从本地文件读取内容
python3 {baseDir}/scripts/files.py edit /www/test.txt -f ./content.txt

# 从标准输入读取
cat ./content.txt | python3 {baseDir}/scripts/files.py edit /www/test.txt
```

### 创建目录/文件

```bash
# 创建目录
python3 {baseDir}/scripts/files.py mkdir /www/newdir

# 创建文件
python3 {baseDir}/scripts/files.py touch /www/test.txt
```

### 删除文件/目录

```bash
# 删除文件
python3 {baseDir}/scripts/files.py rm /www/test.txt

# 删除目录
python3 {baseDir}/scripts/files.py rmdir /www/olddir
```

### 查看/修改权限

```bash
# 查看权限
python3 {baseDir}/scripts/files.py stat /www/test.txt

# 修改权限
python3 {baseDir}/scripts/files.py chmod 755 /www/test.txt

# 修改权限并设置所有者
python3 {baseDir}/scripts/files.py chmod 755 /www/test.txt -u www -g www

# 递归修改目录权限
python3 {baseDir}/scripts/files.py chmod 755 /www/wwwroot -R
```

## 参数说明

### 全局参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--server`, `-s` | 指定服务器名称 | 默认服务器 |

### ls 命令参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `path` | 目录路径 | /www |
| `--page`, `-p` | 页码 | 1 |
| `--rows`, `-r` | 每页显示数量 | 500 |

### cat 命令参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `path` | 文件路径 | 必填 |
| `--lines`, `-n` | 显示最后 N 行 | 全部 |
| `--verbose`, `-v` | 显示文件信息 | 否 |

### edit 命令参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `path` | 文件路径 | 必填 |
| `content` | 文件内容 | 从 stdin 读取 |
| `--file`, `-f` | 从本地文件读取内容 | 无 |
| `--encoding`, `-e` | 文件编码 | utf-8 |

### mkdir 命令参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `path` | 目录路径 | 必填 |

### touch 命令参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `path` | 文件路径 | 必填 |

### rm 命令参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `path` | 文件路径 | 必填 |

### rmdir 命令参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `path` | 目录路径 | 必填 |

### stat 命令参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `path` | 文件路径 | 必填 |

### chmod 命令参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `access` | 权限码（如 755, 644） | 必填 |
| `path` | 文件路径 | 必填 |
| `--user`, `-u` | 所有者用户名 | 当前用户 |
| `--group`, `-g` | 用户组名 | 当前组 |
| `--recursive`, `-R` | 递归设置子目录和文件 | 否 |

## 功能特性说明

### 目录浏览

- 支持分页浏览大目录
- 显示文件/目录的详细信息（名称、大小、权限、所有者、修改时间）
- 自动区分目录和文件
- 支持 URL 编码路径（自动处理含空格和特殊字符的路径）

### 文件读取

- 支持大文件读取
- 支持指定显示行数（类似 `tail` 命令）
- 返回文件编码、大小、只读状态等元信息
- 自动检测文件编码

### 文件编辑

- 支持直接指定内容保存
- 支持从本地文件读取内容
- 支持从标准输入读取内容
- 并发保护：保存时检查文件是否被修改（通过 `st_mtime` 参数）

### 目录/文件管理

- 创建空目录
- 创建空文件
- 删除文件（移动到回收站）
- 删除目录（移动到回收站）

### 权限管理

- 查看文件权限（权限码、所有者）
- 修改文件权限码
- 修改文件所有者
- 修改文件用户组
- 递归设置目录及子文件权限

## 注意事项

1. **路径安全**：所有路径参数会自动进行 URL 编码，支持含空格和特殊字符的路径

2. **删除操作**：删除文件/目录会移动到回收站，非永久删除。如需永久删除需在宝塔面板中清空回收站

3. **并发保护**：保存文件时会自动检查文件是否被其他进程修改，如有冲突会提示

4. **权限要求**：需要对目标路径有相应的读写权限，否则操作会失败

5. **敏感文件**：部分系统文件可能因权限限制无法读取或修改

6. **文件大小限制**：过大的文件可能导致读取/保存超时，建议分批处理

7. **文件下载 API**：宝塔面板 `/files?action=DownloadFile` API 必须传递 `filename` 参数，否则返回 HTTP 500 错误。脚本已自动从 URL 提取文件名，无需手动指定

## 响应格式

### 目录列表响应

```json
{
  "dir": [
    {"nm": "目录名", "sz": "大小", "mt": "时间戳", "acc": "权限", "user": "所有者"}
  ],
  "files": [
    {"nm": "文件名", "sz": "大小", "mt": "时间戳", "acc": "权限", "user": "所有者", "rmk": "备注"}
  ],
  "path": "/www",
  "page": "页码信息"
}
```

### 文件内容响应

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

### 权限信息响应

```json
{
  "chmod": "755",
  "chown": "www:www"
}
```

## 配置说明

技能包复用 `btpanel` 技能的配置系统，配置文件位置：

- 全局配置：`~/.openclaw/bt-skills.yaml`
- 本地配置：`config/servers.local.yaml`
- 默认配置：`config/servers.yaml`

**配置示例**：

```yaml
servers:
  - name: prod-01
    host: https://panel.example.com:8888
    token: YOUR_API_TOKEN
    disabled: false

global:
  timeout: 30
  thresholds:
    cpu: 80
    memory: 85
    disk: 90
```
