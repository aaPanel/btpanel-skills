"""
bt-common 公共模块
提供宝塔API客户端、配置管理和工具函数
"""

from .api_endpoints import (
    API_ENDPOINTS,
    API_GROUPS,
    API_DESCRIPTIONS,
    MIN_PANEL_VERSION,
    get_endpoint,
    get_endpoints_by_group,
    list_endpoints,
    get_endpoint_description,
)
from .bt_client import (
    BtClient,
    BtClientManager,
    sign_request,
)
from .config import (
    Config,
    ServerConfig,
    ThresholdConfig,
    GlobalConfig,
    MIN_PANEL_VERSION as CONFIG_MIN_PANEL_VERSION,
    GLOBAL_CONFIG_FILE,
    load_config,
    load_config_object,
    get_servers,
    get_thresholds,
    find_config_file,
    get_global_config_path,
    create_default_global_config,
    add_server,
    remove_server,
    update_thresholds,
    get_config_info,
)
from .utils import (
    Alert,
    format_bytes,
    format_uptime,
    format_timestamp,
    parse_system_monitor_data,
    check_thresholds,
    format_security_report,
    format_service_status,
    print_table,
    output_result,
    generate_summary_report,
)

__all__ = [
    # API端点
    "API_ENDPOINTS",
    "API_GROUPS",
    "API_DESCRIPTIONS",
    "MIN_PANEL_VERSION",
    "get_endpoint",
    "get_endpoints_by_group",
    "list_endpoints",
    "get_endpoint_description",
    # 客户端
    "BtClient",
    "BtClientManager",
    "sign_request",
    # 配置
    "Config",
    "ServerConfig",
    "ThresholdConfig",
    "GlobalConfig",
    "CONFIG_MIN_PANEL_VERSION",
    "GLOBAL_CONFIG_FILE",
    "load_config",
    "load_config_object",
    "get_servers",
    "get_thresholds",
    "find_config_file",
    "get_global_config_path",
    "create_default_global_config",
    "add_server",
    "remove_server",
    "update_thresholds",
    "get_config_info",
    # 工具
    "Alert",
    "format_bytes",
    "format_uptime",
    "format_timestamp",
    "parse_system_monitor_data",
    "check_thresholds",
    "format_security_report",
    "format_service_status",
    "print_table",
    "output_result",
    "generate_summary_report",
]
