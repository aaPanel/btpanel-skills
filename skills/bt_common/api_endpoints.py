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
    "SYSTEM_STATUS": "/system?action=GetNetWork",  # 综合监控数据接口

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

    # 网站管理 - PHP项目（传统网站）
    "SITE_LIST": "/datalist/data/get_data_list",  # 需要参数 table=sites

    # 项目管理 - 不同类型的项目有不同端点
    "PROJECT_JAVA_LIST": "/mod/java/project/project_list",
    "PROJECT_NODE_LIST": "/project/nodejs/get_project_list",
    "PROJECT_GO_LIST": "/project/go/get_project_list",
    "PROJECT_PYTHON_LIST": "/project/python/GetProjectList",
    "PROJECT_NET_LIST": "/project/net/get_project_list",

    # 数据库
    "DATABASE_LIST": "/database?action=GetDatabases",

    # 任务管理
    "TASK_LIST": "/task?action=GetTaskList",
}

# API 端点分组
API_GROUPS = {
    "system": ["SYSTEM_STATUS"],
    "logs": ["PANEL_LOGS", "ERROR_LOGS", "SITE_LOGS"],
    "security": ["FIREWALL_STATUS", "SECURITY_LOGS", "SSH_INFO"],
    "service": ["SERVICE_LIST", "SERVICE_STATUS"],
    "site": ["SITE_LIST", "PROJECT_JAVA_LIST", "PROJECT_NODE_LIST", "PROJECT_GO_LIST", "PROJECT_PYTHON_LIST", "PROJECT_NET_LIST"],
    "database": ["DATABASE_LIST"],
    "task": ["TASK_LIST"],
}

# 端点说明
API_DESCRIPTIONS = {
    "SYSTEM_STATUS": "获取系统综合监控数据（CPU、内存、磁盘、网络、负载等）",
    "PANEL_LOGS": "获取面板操作日志",
    "ERROR_LOGS": "获取错误日志",
    "SITE_LOGS": "获取网站日志",
    "FIREWALL_STATUS": "获取防火墙状态",
    "SECURITY_LOGS": "获取安全日志",
    "SSH_INFO": "获取SSH配置信息",
    "SERVICE_LIST": "获取服务列表",
    "SERVICE_STATUS": "获取服务状态",
    "SITE_LIST": "获取PHP网站列表（传统网站）",
    "PROJECT_JAVA_LIST": "获取Java项目列表",
    "PROJECT_NODE_LIST": "获取Node.js项目列表",
    "PROJECT_GO_LIST": "获取Go项目列表",
    "PROJECT_PYTHON_LIST": "获取Python项目列表",
    "PROJECT_NET_LIST": "获取.NET项目列表",
    "DATABASE_LIST": "获取数据库列表",
    "TASK_LIST": "获取任务列表",
}

# 项目类型映射
PROJECT_TYPES = {
    "PHP": "SITE_LIST",
    "Java": "PROJECT_JAVA_LIST",
    "Node": "PROJECT_NODE_LIST",
    "Go": "PROJECT_GO_LIST",
    "Python": "PROJECT_PYTHON_LIST",
    "net": "PROJECT_NET_LIST",
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
