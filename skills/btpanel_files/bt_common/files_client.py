#!/usr/bin/env python3
# coding: utf-8
"""
宝塔文件操作客户端
封装宝塔面板文件管理 API 接口
"""

import json
import urllib.parse
import warnings
from typing import Optional, Dict, Any, List

# 禁用 SSL 警告
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

from .bt_client import BtClient, BtClientManager
from .config import get_servers, ServerConfig


def get_server_config(server_name: str = None) -> Optional[Dict]:
    """
    获取服务器配置

    Args:
        server_name: 服务器名称，为 None 时返回第一个启用的服务器

    Returns:
        服务器配置字典或 None
    """
    servers = get_servers()
    if not servers:
        return None

    if server_name:
        for server in servers:
            # 兼容 ServerConfig 对象和字典两种格式
            name = server.name if hasattr(server, 'name') and hasattr(server, 'host') else server.get('name')
            if name == server_name:
                # 如果是 ServerConfig 对象，转换为字典返回
                if hasattr(server, 'name') and hasattr(server, 'host'):
                    return {
                        'name': server.name,
                        'host': server.host,
                        'token': server.token,
                        'timeout': server.timeout,
                        'enabled': server.enabled,
                        'verify_ssl': server.verify_ssl if hasattr(server, 'verify_ssl') else True
                    }
                return server
        return None

    # 返回第一个启用的服务器
    for server in servers:
        # 兼容 ServerConfig 对象和字典两种格式
        enabled = server.enabled if hasattr(server, 'enabled') and hasattr(server, 'host') else server.get('enabled', True)
        if enabled:
            # 如果是 ServerConfig 对象，转换为字典返回
            if hasattr(server, 'name') and hasattr(server, 'host'):
                return {
                    'name': server.name,
                    'host': server.host,
                    'token': server.token,
                    'timeout': server.timeout,
                    'enabled': server.enabled,
                    'verify_ssl': server.verify_ssl if hasattr(server, 'verify_ssl') else True
                }
            return server

    return None


class FilesClient:
    """宝塔文件操作客户端"""

    def __init__(self, server_name: str = None):
        """
        初始化文件客户端

        Args:
            server_name: 服务器名称，为 None 时使用默认服务器
        """
        self.server_name = server_name
        self.client = None
        self._init_client()

    def _init_client(self):
        """初始化 API 客户端"""
        if self.server_name:
            config = get_server_config(self.server_name)
            if not config:
                raise ValueError(f"未找到服务器配置：{self.server_name}")
            self.client = BtClient(
                name=config.get('name', self.server_name),
                host=config['host'],
                token=config['token'],
                timeout=config.get('timeout', 10000),
                verify_ssl=config.get('verify_ssl', True)
            )
        else:
            # 使用默认服务器
            manager = BtClientManager()
            self.client = manager.get_client()

    def _encode_path(self, path: str) -> str:
        """URL 编码路径"""
        return urllib.parse.quote(path, safe='')

    def get_dir(self, path: str = "/www", page: int = 1, show_row: int = 500) -> Dict[str, Any]:
        """
        获取目录信息

        Args:
            path: 目录路径
            page: 页码
            show_row: 每页显示数量

        Returns:
            目录信息字典，包含 dir（目录列表）和 files（文件列表）
        """
        encoded_path = self._encode_path(path)
        endpoint = f"/files?action=GetDirNew&path={encoded_path}&p={page}&showRow={show_row}"
        return self.client.request(endpoint)

    def get_file_body(self, path: str) -> Dict[str, Any]:
        """
        读取文件内容

        Args:
            path: 文件路径

        Returns:
            文件内容字典，包含 data、encoding、size 等字段
        """
        encoded_path = self._encode_path(path)
        endpoint = f"/files?action=GetFileBody&path={encoded_path}"
        return self.client.request(endpoint)

    def save_file_body(self, path: str, data: str, encoding: str = "utf-8",
                       st_mtime: str = None, force: bool = False) -> Dict[str, Any]:
        """
        保存文件内容

        Args:
            path: 文件路径
            data: 文件内容
            encoding: 文件编码
            st_mtime: 文件修改时间戳（用于并发检测）
            force: 是否强制保存

        Returns:
            保存结果字典
        """
        encoded_path = self._encode_path(path)

        # 使用 POST body 发送数据，避免 URL 过长问题
        params = {
            "path": path,
            "data": data,
            "encoding": encoding
        }
        if st_mtime:
            params["st_mtime"] = st_mtime
        if force:
            params["force"] = "1"

        endpoint = f"/files?action=SaveFileBody"
        return self.client.request(endpoint, params)

    def create_dir(self, path: str) -> Dict[str, Any]:
        """
        创建目录

        Args:
            path: 目录路径

        Returns:
            创建结果字典
        """
        encoded_path = self._encode_path(path)
        endpoint = f"/files?action=CreateDir&path={encoded_path}"
        return self.client.request(endpoint)

    def create_file(self, path: str) -> Dict[str, Any]:
        """
        创建文件

        Args:
            path: 文件路径

        Returns:
            创建结果字典
        """
        encoded_path = self._encode_path(path)
        endpoint = f"/files?action=CreateFile&path={encoded_path}"
        return self.client.request(endpoint)

    def delete_dir(self, path: str) -> Dict[str, Any]:
        """
        删除目录（移动到回收站）

        Args:
            path: 目录路径

        Returns:
            删除结果字典
        """
        encoded_path = self._encode_path(path)
        endpoint = f"/files?action=DeleteDir&path={encoded_path}"
        return self.client.request(endpoint)

    def delete_file(self, path: str) -> Dict[str, Any]:
        """
        删除文件（移动到回收站）

        Args:
            path: 文件路径

        Returns:
            删除结果字典
        """
        encoded_path = self._encode_path(path)
        endpoint = f"/files?action=DeleteFile&path={encoded_path}"
        return self.client.request(endpoint)

    def get_file_access(self, filename: str) -> Dict[str, Any]:
        """
        获取文件权限

        Args:
            filename: 文件路径

        Returns:
            权限信息字典，包含 chmod 和 chown
        """
        encoded_filename = self._encode_path(filename)
        endpoint = f"/files?action=GetFileAccess&filename={encoded_filename}"
        return self.client.request(endpoint)

    def set_file_access(self, filename: str, access: str, user: str = "www",
                        group: str = "www", all_files: bool = False) -> Dict[str, Any]:
        """
        设置文件权限

        Args:
            filename: 文件路径
            access: 权限码（如 755, 644）
            user: 所有者用户名（默认 www）
            group: 用户组名（默认 www）
            all_files: 是否递归设置子目录和文件

        Returns:
            设置结果字典
        """
        # 宝塔 SetFileAccess API 需要 filename, access, user, group 参数
        # 注意：user 和 group 必须同时提供，否则会失败
        params = {
            "filename": filename,
            "access": access,
            "user": user,
            "group": group
        }
        if all_files:
            params["all"] = "1"

        endpoint = f"/files?action=SetFileAccess"
        return self.client.request(endpoint, params)

    # ==================== 便捷方法 ====================

    def read_file(self, path: str) -> str:
        """
        便捷方法：直接读取文件内容返回字符串

        Args:
            path: 文件路径

        Returns:
            文件内容字符串
        """
        result = self.get_file_body(path)
        if result.get('status') or result.get('only_read') is False:
            return result.get('data', '')
        raise Exception(result.get('msg', '读取文件失败'))

    def write_file(self, path: str, content: str, encoding: str = "utf-8") -> bool:
        """
        便捷方法：写入文件内容

        Args:
            path: 文件路径
            content: 文件内容
            encoding: 文件编码

        Returns:
            是否成功
        """
        # 先获取当前文件信息以获取 st_mtime
        try:
            file_info = self.get_file_body(path)
            st_mtime = file_info.get('st_mtime')
        except:
            st_mtime = None

        result = self.save_file_body(path, content, encoding, st_mtime)
        return result.get('status', False)

    def list_dir(self, path: str = "/www") -> Dict[str, List]:
        """
        便捷方法：获取目录列表

        Args:
            path: 目录路径

        Returns:
            包含 directories 和 files 的字典
        """
        result = self.get_dir(path)
        return {
            'directories': result.get('dir', []),
            'files': result.get('files', []),
            'path': result.get('path', path)
        }


class FilesClientManager:
    """文件客户端管理器 - 支持多服务器"""

    def __init__(self):
        self._clients: Dict[str, FilesClient] = {}

    def get_client(self, server_name: str = None) -> FilesClient:
        """
        获取文件客户端

        Args:
            server_name: 服务器名称

        Returns:
            FilesClient 实例
        """
        if server_name is None:
            server_name = "_default"

        if server_name not in self._clients:
            self._clients[server_name] = FilesClient(server_name if server_name != "_default" else None)

        return self._clients[server_name]

    def list_servers(self) -> List[str]:
        """列出所有可用的服务器"""
        config = get_servers()
        return [s.get('name') for s in config] if config else []
