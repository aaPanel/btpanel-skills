# /// script
# dependencies = [
#   "requests>=2.28",
#   "pyyaml>=6.0",
# ]
# ///
"""
宝塔面板API客户端
支持多服务器管理和API请求封装
"""

import hashlib
import time
from dataclasses import dataclass, field
from typing import Any, Optional
from urllib.parse import urlencode

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# 宝塔API端点定义
API_ENDPOINTS = {
    # 系统状态
    "SYSTEM_STATUS": "/system?action=GetSystemTotal",
    "SYSTEM_INFO": "/system?action=GetSystemTotal",
    "NETWORK_INFO": "/system?action=GetNetWork",
    # 日志相关
    "PANEL_LOGS": "/logs?action=GetLogs",
    "ERROR_LOGS": "/site?action=GetErrorLog",
    "SITE_LOGS": "/site?action=GetSiteLogs",
    # 安全相关
    "FIREWALL_STATUS": "/safe?action=GetFirewallStatus",
    "SECURITY_LOGS": "/safe?action=GetLogs",
    "SSH_INFO": "/safe?action=GetSshInfo",
    # 服务管理
    "SERVICE_LIST": "/system?action=GetServiceList",
    "SERVICE_STATUS": "/system?action=GetServiceStatus",
    # 网站管理
    "SITE_LIST": "/site?action=GetSiteList",
    "SITE_STATUS": "/site?action=GetSiteStatus",
    # 数据库
    "DATABASE_LIST": "/database?action=GetDatabases",
    # 任务管理
    "TASK_LIST": "/task?action=GetTaskList",
}


def sign_request(token: str, params: Optional[dict] = None) -> dict:
    """
    生成API请求签名
    宝塔API使用 MD5(time + MD5(token)) 的签名机制

    Args:
        token: 宝塔面板API Token
        params: 请求参数

    Returns:
        包含签名的完整参数
    """
    if params is None:
        params = {}

    request_time = int(time.time())
    # 签名算法: request_token = md5(request_time + md5(token))
    token_md5 = hashlib.md5(token.encode()).hexdigest()
    request_token = hashlib.md5(f"{request_time}{token_md5}".encode()).hexdigest()

    return {
        **params,
        "request_time": request_time,
        "request_token": request_token,
    }


@dataclass
class ServerConfig:
    """服务器配置"""

    name: str
    host: str
    token: str
    timeout: int = 10000
    enabled: bool = True


@dataclass
class BtClient:
    """
    宝塔面板客户端类

    Attributes:
        name: 服务器名称
        host: 面板地址
        token: API Token
        timeout: 请求超时时间（毫秒）
    """

    name: str
    host: str
    token: str
    timeout: int = 10000
    enabled: bool = True
    _session: requests.Session = field(default=None, repr=False, compare=False)  # type: ignore

    def __post_init__(self):
        # 移除末尾斜杠
        self.host = self.host.rstrip("/")
        # 创建session
        self._session = requests.Session()
        # 配置重试策略
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry)
        self._session.mount("https://", adapter)
        self._session.mount("http://", adapter)
        # 设置默认headers
        self._session.headers.update(
            {"Content-Type": "application/x-www-form-urlencoded"}
        )
        # 禁用SSL警告（宝塔面板默认使用自签名证书）
        self._session.verify = False

    def request(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """
        发送API请求

        Args:
            endpoint: API端点
            params: 请求参数

        Returns:
            API响应数据

        Raises:
            ConnectionError: 无法连接到服务器
            TimeoutError: 请求超时
            RuntimeError: API请求失败
        """
        signed_params = sign_request(self.token, params)
        url = f"{self.host}{endpoint}"

        try:
            response = self._session.post(
                url,
                data=urlencode(signed_params),
                timeout=self.timeout / 1000,
            )
            response.raise_for_status()
            data = response.json()

            # 检查宝塔API响应状态
            if data.get("status") is False:
                raise RuntimeError(data.get("msg", "API请求失败"))

            return data

        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"无法连接到服务器: {self.host}")
        except requests.exceptions.Timeout:
            raise TimeoutError(f"请求超时: {self.host}")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"请求失败: {e}")

    def get_system_status(self) -> dict:
        """获取系统状态"""
        return self.request(API_ENDPOINTS["SYSTEM_STATUS"])

    def get_network_info(self) -> dict:
        """获取网络信息"""
        return self.request(API_ENDPOINTS["NETWORK_INFO"])

    def get_service_list(self) -> list:
        """获取服务列表"""
        result = self.request(API_ENDPOINTS["SERVICE_LIST"])
        return result if isinstance(result, list) else result.get("data", [])

    def get_site_list(self) -> list:
        """获取网站列表"""
        result = self.request(API_ENDPOINTS["SITE_LIST"])
        return result if isinstance(result, list) else result.get("data", [])

    def get_database_list(self) -> list:
        """获取数据库列表"""
        result = self.request(API_ENDPOINTS["DATABASE_LIST"])
        return result if isinstance(result, list) else result.get("data", [])

    def get_firewall_status(self) -> dict:
        """获取防火墙状态"""
        return self.request(API_ENDPOINTS["FIREWALL_STATUS"])

    def get_security_logs(self, page: int = 1, limit: int = 20) -> dict:
        """
        获取安全日志

        Args:
            page: 页码
            limit: 每页数量
        """
        return self.request(API_ENDPOINTS["SECURITY_LOGS"], {"page": page, "limit": limit})

    def get_ssh_info(self) -> dict:
        """获取SSH信息"""
        return self.request(API_ENDPOINTS["SSH_INFO"])

    def get_panel_logs(self, page: int = 1, limit: int = 20) -> dict:
        """
        获取面板操作日志

        Args:
            page: 页码
            limit: 每页数量
        """
        return self.request(API_ENDPOINTS["PANEL_LOGS"], {"page": page, "limit": limit})

    def get_error_logs(self, site_name: str) -> dict:
        """
        获取错误日志

        Args:
            site_name: 网站名称
        """
        return self.request(API_ENDPOINTS["ERROR_LOGS"], {"siteName": site_name})

    def get_task_list(self) -> dict:
        """获取任务列表"""
        return self.request(API_ENDPOINTS["TASK_LIST"])

    def health_check(self) -> bool:
        """
        健康检查

        Returns:
            是否连接成功
        """
        try:
            self.get_system_status()
            return True
        except Exception:
            return False

    def close(self):
        """关闭连接"""
        self._session.close()


class BtClientManager:
    """多服务器管理器"""

    def __init__(self):
        self.clients: dict[str, BtClient] = {}
        self.config: Optional[dict] = None
        self.global_config: dict = {
            "retryCount": 3,
            "retryDelay": 1000,
            "concurrency": 3,
            "thresholds": {"cpu": 80, "memory": 85, "disk": 90},
        }

    def load_config(self, config_path: Optional[str] = None) -> "BtClientManager":
        """
        从配置文件加载服务器

        Args:
            config_path: 配置文件路径

        Returns:
            self，支持链式调用
        """
        from .config import load_config

        self.config = load_config(config_path)

        # 加载全局配置
        if "global" in self.config:
            self.global_config.update(self.config["global"])

        # 初始化所有服务器客户端
        for server in self.config.get("servers", []):
            if server.get("enabled", True):
                client = BtClient(
                    name=server["name"],
                    host=server["host"],
                    token=server["token"],
                    timeout=server.get("timeout", 10000),
                )
                self.clients[server["name"]] = client

        return self

    def get_global_config(self) -> dict:
        """获取全局配置"""
        return self.global_config

    def get_client(self, name: str) -> BtClient:
        """
        获取客户端

        Args:
            name: 服务器名称

        Returns:
            宝塔客户端实例

        Raises:
            KeyError: 未找到服务器
        """
        if name not in self.clients:
            raise KeyError(f"未找到服务器: {name}")
        return self.clients[name]

    def get_all_clients(self) -> dict[str, BtClient]:
        """获取所有客户端"""
        return self.clients

    def add_server(self, config: dict) -> BtClient:
        """
        添加服务器

        Args:
            config: 服务器配置
        """
        client = BtClient(
            name=config["name"],
            host=config["host"],
            token=config["token"],
            timeout=config.get("timeout", 10000),
        )
        self.clients[config["name"]] = client
        return client

    def remove_server(self, name: str):
        """
        移除服务器

        Args:
            name: 服务器名称
        """
        if name in self.clients:
            self.clients[name].close()
            del self.clients[name]

    def get_server_list(self) -> list[str]:
        """获取服务器列表"""
        return list(self.clients.keys())

    def execute_all(self, action) -> dict[str, Any]:
        """
        并行执行所有服务器的操作

        Args:
            action: 异步操作函数，接收BtClient参数

        Returns:
            各服务器的执行结果
        """
        results = {}
        for name, client in self.clients.items():
            try:
                result = action(client)
                results[name] = {"success": True, "data": result}
            except Exception as e:
                results[name] = {"success": False, "error": str(e)}
        return results

    def check_all_connections(self) -> dict[str, bool]:
        """检查所有服务器连接状态"""
        return {name: client.health_check() for name, client in self.clients.items()}

    def close_all(self):
        """关闭所有连接"""
        for client in self.clients.values():
            client.close()
