# /// script
# dependencies = []
# ///
"""
宝塔面板 API 端点定义
定义所有宝塔面板 API 接口路径
"""

# 宝塔面板版本要求
MIN_PANEL_VERSION = "9.0.0"

# API 端点定义
# 格式: 端点路径?动作参数
API_ENDPOINTS = {
    # 系统状态（综合接口，包含CPU、内存、磁盘、网络、负载等）
    "SYSTEM_STATUS": "/system?action=GetSystemTotal",
    "SYSTEM_NETWORK": "/system?action=GetNetWork",  # 综合监控数据接口

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

# API 端点分组
API_GROUPS = {
    "system": ["SYSTEM_STATUS", "SYSTEM_NETWORK"],
    "logs": ["PANEL_LOGS", "ERROR_LOGS", "SITE_LOGS"],
    "security": ["FIREWALL_STATUS", "SECURITY_LOGS", "SSH_INFO"],
    "service": ["SERVICE_LIST", "SERVICE_STATUS"],
    "site": ["SITE_LIST", "SITE_STATUS"],
    "database": ["DATABASE_LIST"],
    "task": ["TASK_LIST"],
}

# 端点说明
API_DESCRIPTIONS = {
    "SYSTEM_STATUS": "获取系统状态（基础信息）",
    "SYSTEM_NETWORK": "获取系统综合监控数据（CPU、内存、磁盘、网络、负载等）",
    "PANEL_LOGS": "获取面板操作日志",
    "ERROR_LOGS": "获取错误日志",
    "SITE_LOGS": "获取网站日志",
    "FIREWALL_STATUS": "获取防火墙状态",
    "SECURITY_LOGS": "获取安全日志",
    "SSH_INFO": "获取SSH配置信息",
    "SERVICE_LIST": "获取服务列表",
    "SERVICE_STATUS": "获取服务状态",
    "SITE_LIST": "获取网站列表",
    "SITE_STATUS": "获取网站状态",
    "DATABASE_LIST": "获取数据库列表",
    "TASK_LIST": "获取任务列表",
}


def get_endpoint(name: str) -> str:
    """
    获取 API 端点路径

    Args:
        name: 端点名称

    Returns:
        端点路径

    Raises:
        KeyError: 端点不存在
    """
    if name not in API_ENDPOINTS:
        raise KeyError(f"未找到 API 端点: {name}")
    return API_ENDPOINTS[name]


def get_endpoints_by_group(group: str) -> dict:
    """
    获取分组下的所有端点

    Args:
        group: 分组名称

    Returns:
        端点字典
    """
    if group not in API_GROUPS:
        return {}
    return {name: API_ENDPOINTS[name] for name in API_GROUPS[group]}


def list_endpoints() -> dict:
    """
    列出所有端点

    Returns:
        端点字典
    """
    return API_ENDPOINTS.copy()


def get_endpoint_description(name: str) -> str:
    """
    获取端点说明

    Args:
        name: 端点名称

    Returns:
        端点说明
    """
    return API_DESCRIPTIONS.get(name, "未知端点")
