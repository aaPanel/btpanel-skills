"""
宝塔API客户端单元测试
"""

import hashlib
import time
from unittest.mock import MagicMock, patch

import pytest

# 添加公共模块路径
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bt_common.bt_client import (
    API_ENDPOINTS,
    BtClient,
    BtClientManager,
    sign_request,
)
from bt_common.config import Config, ServerConfig, ThresholdConfig, load_config
from bt_common.utils import (
    Alert,
    check_thresholds,
    format_bytes,
    parse_system_monitor_data,
    format_uptime,
)


class TestSignRequest:
    """测试API签名功能"""

    def test_sign_request_basic(self):
        """测试基本签名功能"""
        token = "test_token_123"
        params = {"action": "test"}

        result = sign_request(token, params)

        # 验证返回包含必要字段
        assert "request_time" in result
        assert "request_token" in result
        assert "action" in result
        assert result["action"] == "test"

    def test_sign_request_empty_params(self):
        """测试空参数签名"""
        token = "test_token_123"
        result = sign_request(token)

        assert "request_time" in result
        assert "request_token" in result

    def test_sign_request_format(self):
        """测试签名格式正确性"""
        token = "test_token_123"
        result = sign_request(token)

        # 验证签名算法: request_token = md5(time + md5(token))
        request_time = result["request_time"]
        request_token = result["request_token"]

        expected_token = hashlib.md5(f"{request_time}{hashlib.md5(token.encode()).hexdigest()}".encode()).hexdigest()
        assert request_token == expected_token


class TestBtClient:
    """测试宝塔客户端"""

    def test_client_initialization(self):
        """测试客户端初始化"""
        client = BtClient(
            name="test-server",
            host="https://example.com:8888",
            token="test_token",
        )

        assert client.name == "test-server"
        assert client.host == "https://example.com:8888"
        assert client.token == "test_token"
        assert client.timeout == 10000
        assert client.enabled is True

    def test_client_host_trailing_slash(self):
        """测试主机地址末尾斜杠处理"""
        client = BtClient(
            name="test",
            host="https://example.com:8888/",
            token="test_token",
        )

        assert client.host == "https://example.com:8888"

    def test_client_custom_timeout(self):
        """测试自定义超时"""
        client = BtClient(
            name="test",
            host="https://example.com:8888",
            token="test_token",
            timeout=5000,
        )

        assert client.timeout == 5000

    @patch("bt_common.bt_client.requests.Session")
    def test_health_check_success(self, mock_session_class):
        """测试健康检查成功"""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": True, "cpu_usage": 50}
        mock_session.post.return_value = mock_response
        mock_session_class.return_value = mock_session

        client = BtClient(
            name="test",
            host="https://example.com:8888",
            token="test_token",
        )

        result = client.health_check()
        assert result is True

    @patch("bt_common.bt_client.requests.Session")
    def test_health_check_failure(self, mock_session_class):
        """测试健康检查失败"""
        mock_session = MagicMock()
        mock_session.post.side_effect = Exception("Connection error")
        mock_session_class.return_value = mock_session

        client = BtClient(
            name="test",
            host="https://example.com:8888",
            token="test_token",
        )

        result = client.health_check()
        assert result is False


class TestBtClientManager:
    """测试客户端管理器"""

    def test_manager_initialization(self):
        """测试管理器初始化"""
        manager = BtClientManager()

        assert manager.clients == {}
        assert manager.config is None

    def test_add_server(self):
        """测试添加服务器"""
        manager = BtClientManager()

        client = manager.add_server({
            "name": "test-server",
            "host": "https://example.com:8888",
            "token": "test_token",
        })

        assert "test-server" in manager.clients
        assert client.name == "test-server"

    def test_remove_server(self):
        """测试移除服务器"""
        manager = BtClientManager()

        manager.add_server({
            "name": "test-server",
            "host": "https://example.com:8888",
            "token": "test_token",
        })

        manager.remove_server("test-server")
        assert "test-server" not in manager.clients

    def test_get_client(self):
        """测试获取客户端"""
        manager = BtClientManager()

        manager.add_server({
            "name": "test-server",
            "host": "https://example.com:8888",
            "token": "test_token",
        })

        client = manager.get_client("test-server")
        assert client.name == "test-server"

    def test_get_client_not_found(self):
        """测试获取不存在的客户端"""
        manager = BtClientManager()

        with pytest.raises(KeyError):
            manager.get_client("non-existent")

    def test_get_server_list(self):
        """测试获取服务器列表"""
        manager = BtClientManager()

        manager.add_server({
            "name": "server-1",
            "host": "https://example1.com:8888",
            "token": "token1",
        })
        manager.add_server({
            "name": "server-2",
            "host": "https://example2.com:8888",
            "token": "token2",
        })

        servers = manager.get_server_list()
        assert len(servers) == 2
        assert "server-1" in servers
        assert "server-2" in servers

    def test_get_global_config_default(self):
        """测试获取默认全局配置"""
        manager = BtClientManager()
        config = manager.get_global_config()

        assert config["retryCount"] == 3
        assert config["retryDelay"] == 1000
        assert config["concurrency"] == 3
        assert config["thresholds"]["cpu"] == 80


class TestConfig:
    """测试配置模块"""

    def test_threshold_config_defaults(self):
        """测试默认阈值配置"""
        config = ThresholdConfig()

        assert config.cpu == 80
        assert config.memory == 85
        assert config.disk == 90

    def test_server_config(self):
        """测试服务器配置"""
        config = ServerConfig(
            name="test",
            host="https://example.com:8888",
            token="test_token",
        )

        assert config.name == "test"
        assert config.host == "https://example.com:8888"
        assert config.token == "test_token"
        assert config.timeout == 10000
        assert config.enabled is True

    def test_config_from_dict(self):
        """测试从字典创建配置"""
        data = {
            "servers": [
                {
                    "name": "server-1",
                    "host": "https://example.com:8888",
                    "token": "token1",
                }
            ],
            "global": {
                "thresholds": {
                    "cpu": 90,
                    "memory": 95,
                    "disk": 98,
                }
            },
        }

        config = Config.from_dict(data)

        assert len(config.servers) == 1
        assert config.servers[0].name == "server-1"
        assert config.global_config.thresholds.cpu == 90


class TestUtils:
    """测试工具函数"""

    def test_format_bytes(self):
        """测试字节格式化"""
        assert format_bytes(0) == "0 B"
        assert format_bytes(1024) == "1.00 KB"
        assert format_bytes(1024 * 1024) == "1.00 MB"
        assert format_bytes(1024 * 1024 * 1024) == "1.00 GB"

    def test_format_bytes_decimals(self):
        """测试字节格式化小数位"""
        result = format_bytes(1536, decimals=0)  # 1.5 KB
        assert result == "2 KB"  # 四舍五入

    def test_format_uptime(self):
        """测试运行时间格式化"""
        assert format_uptime(60) == "1分钟"
        assert format_uptime(3600) == "1小时0分钟"
        assert format_uptime(86400) == "1天0小时"
        assert format_uptime(90061) == "1天1小时"

    def test_parse_system_monitor_data(self):
        """测试系统监控数据解析"""
        # 模拟实际API返回数据
        data = {
            "cpu": [9.0, 2, [35.2, 18.8], "Common KVM processor * 1", 2, 1],
            "cpu_times": {"user": 22.4, "system": 4.5, "idle": 73.2, "iowait": 0.0},
            "load": {"one": 0.06, "five": 0.09, "fifteen": 0.05, "max": 4, "safe": 3.0},
            "mem": {"memTotal": 1967, "memFree": 540, "memCached": 692, "memAvailable": 1035, "memRealUsed": 735},
            "disk": [
                {
                    "path": "/",
                    "size": ["39.0 GB", "35.0 GB", "4.0 GB", "89.75%", "0.00 b", "35.0"],
                    "filesystem": "/dev/sda2",
                    "type": "xfs",
                    "byte_size": [41881174016, 37587406848, 4293767168],
                }
            ],
            "network": {"lo": {"upTotal": 735440231, "downTotal": 735440231}},
            "upTotal": 14243522823,
            "downTotal": 76538967320,
            "up": 2.22,
            "down": 6.56,
            "title": "test-server",
            "system": "Debian GNU/Linux 12 (bookworm) x86_64(Py3.7.16)",
            "simple_system": "Debian 12",
            "time": "150天",
            "version": "11.6.0",
            "site_total": 13,
            "database_total": 3,
            "ftp_total": 0,
        }

        result = parse_system_monitor_data(data, "test-server")

        assert result["server"] == "test-server"
        assert "timestamp" in result
        assert result["cpu"]["usage"] == 9.0
        assert result["cpu"]["cores"] == 2
        assert result["memory"]["total_mb"] == 1967
        assert result["memory"]["percent"] > 0
        assert result["disk"]["percent"] > 0
        assert result["hostname"] == "test-server"
        assert result["version"] == "11.6.0"
        assert result["resources"]["sites"] == 13
        assert result["resources"]["databases"] == 3

    def test_check_thresholds_no_alerts(self):
        """测试阈值检查无告警"""
        metrics = {
            "cpu": {"usage": 50},
            "memory": {"percent": 60, "total_mb": 2048, "used_mb": 1229},
            "disk": {"percent": 70, "disks": []},
            "load": {"one_minute": 0.5, "cpu_count": 4},
        }
        thresholds = {"cpu": 80, "memory": 85, "disk": 90}

        alerts = check_thresholds(metrics, thresholds)

        assert len(alerts) == 0

    def test_check_thresholds_cpu_alert(self):
        """测试CPU告警"""
        metrics = {
            "cpu": {"usage": 85},
            "memory": {"percent": 60, "total_mb": 2048, "used_mb": 1229},
            "disk": {"percent": 70, "disks": []},
            "load": {"one_minute": 0.5, "cpu_count": 4},
        }
        thresholds = {"cpu": 80, "memory": 85, "disk": 90}

        alerts = check_thresholds(metrics, thresholds)

        assert len(alerts) == 1
        assert alerts[0].type == "cpu"
        assert alerts[0].level == "warning"

    def test_check_thresholds_multiple_alerts(self):
        """测试多个告警"""
        metrics = {
            "cpu": {"usage": 85},
            "memory": {"percent": 90, "total_mb": 2048, "used_mb": 1843},
            "disk": {"percent": 95, "disks": []},
            "load": {"one_minute": 0.5, "cpu_count": 4},
        }
        thresholds = {"cpu": 80, "memory": 85, "disk": 90}

        alerts = check_thresholds(metrics, thresholds)

        assert len(alerts) == 3
        # 磁盘告警应该是critical
        disk_alerts = [a for a in alerts if a.type == "disk"]
        assert len(disk_alerts) == 1
        assert disk_alerts[0].level == "critical"


class TestAlert:
    """测试告警类"""

    def test_alert_creation(self):
        """测试告警创建"""
        alert = Alert(
            level="warning",
            type="cpu",
            message="CPU使用率过高",
            value=85.5,
        )

        assert alert.level == "warning"
        assert alert.type == "cpu"
        assert alert.message == "CPU使用率过高"
        assert alert.value == 85.5


class TestAPIEndpoints:
    """测试API端点"""

    def test_endpoints_exist(self):
        """测试端点定义存在"""
        assert "SYSTEM_STATUS" in API_ENDPOINTS
        assert "FIREWALL_STATUS" in API_ENDPOINTS
        assert "SSH_INFO" in API_ENDPOINTS
        assert "SERVICE_LIST" in API_ENDPOINTS
        assert "SITE_LIST" in API_ENDPOINTS
        assert "DATABASE_LIST" in API_ENDPOINTS

    def test_endpoints_format(self):
        """测试端点格式"""
        for name, endpoint in API_ENDPOINTS.items():
            assert endpoint.startswith("/"), f"{name} 端点应以 / 开头"
            # 部分端点使用路径形式而非action参数
            # 例如: /datalist/data/get_data_list, /project/nodejs/get_project_list

    def test_project_type_endpoints(self):
        """测试项目类型端点存在"""
        from bt_common.api_endpoints import PROJECT_TYPES

        # 测试所有项目类型都有对应的端点
        expected_types = ["PHP", "Java", "Node", "Go", "Python", "net", "Proxy", "HTML", "Other"]
        for ptype in expected_types:
            assert ptype in PROJECT_TYPES, f"项目类型 {ptype} 未定义"
            endpoint_key = PROJECT_TYPES[ptype]
            assert endpoint_key in API_ENDPOINTS, f"端点 {endpoint_key} 不存在"

        # 测试新增的反代、HTML、其他项目端点
        assert "PROJECT_PROXY_LIST" in API_ENDPOINTS
        assert "PROJECT_HTML_LIST" in API_ENDPOINTS
        assert "PROJECT_OTHER_LIST" in API_ENDPOINTS


class TestSiteParsing:
    """测试网站解析功能"""

    def test_parse_proxy_site(self):
        """测试反代项目解析"""
        from bt_common.utils import parse_proxy_site

        proxy_data = {
            "id": 33,
            "name": "panel.proxy.com",
            "path": "/usr/share/nginx/html",
            "status": "1",
            "ps": "nginx配置解析并添加",
            "addtime": "2026-02-26 14:33:20",
            "healthy": 1,
            "waf": {"status": True},
            "conf_path": "/www/server/panel/vhost/nginx/panel.proxy.com.conf",
            "ssl": -1,
            "proxy_pass": "https://127.0.0.1:8888"
        }

        result = parse_proxy_site(proxy_data, "test-server")

        assert result["name"] == "panel.proxy.com"
        assert result["type"] == "Proxy"
        assert result["status"] == "running"
        assert result["healthy"] is True
        assert result["proxy_pass"] == "https://127.0.0.1:8888"
        assert result["waf_enabled"] is True
        assert result["ssl"]["status"] == "none"

    def test_parse_proxy_site_stopped(self):
        """测试已停止的反代项目"""
        from bt_common.utils import parse_proxy_site

        proxy_data = {
            "name": "stopped.proxy.com",
            "status": "0",
            "healthy": 0,
            "ssl": {"endtime": 30},  # 30天过期，属于warning状态
        }

        result = parse_proxy_site(proxy_data, "test-server")

        assert result["status"] == "stopped"
        assert result["healthy"] is False
        assert result["ssl"]["status"] == "warning"  # 30天属于warning

    def test_parse_html_site(self):
        """测试HTML静态项目解析"""
        from bt_common.utils import parse_html_site

        html_data = {
            "id": 21,
            "name": "sdjfg.cimc",
            "path": "/www/wwwroot/sdjfg.cimc",
            "status": "1",
            "ps": "sdjfg.cimc",
            "addtime": "2026-02-24 10:20:07",
            "project_type": "html",
            "ssl": {"endtime": -763, "issuer_O": "Let's Encrypt"},
        }

        result = parse_html_site(html_data, "test-server")

        assert result["name"] == "sdjfg.cimc"
        assert result["type"] == "HTML"
        assert result["status"] == "running"
        assert result["ssl"]["status"] == "expired"
        assert result["ssl"]["days_remaining"] == -763
        assert result["process"] is None

    def test_parse_other_site(self):
        """测试其他项目解析"""
        from bt_common.utils import parse_project_site

        other_data = {
            "id": 47,
            "name": "other_go",
            "path": "/www/wwwroot/dd/OTHER/",
            "status": "1",
            "project_type": "Other",
            "project_config": {
                "port": 17416,
                "domains": [],
            },
            "run": True,
            "load_info": {
                "3183047": {
                    "name": "python3",
                    "pid": 3183047,
                    "status": "睡眠",
                    "memory_used": 10240000,
                    "cpu_percent": 0.04,
                    "threads": 4,
                    "connects": 1,
                }
            },
            "ssl": -1,
        }

        result = parse_project_site(other_data, "test-server")

        assert result["name"] == "other_go"
        assert result["type"] == "Other"
        assert result["status"] == "running"
        assert result["port"] == 17416
        assert result["process"]["pid"] == 3183047
        assert result["process"]["threads"] == 4

    def test_parse_all_sites_with_new_types(self):
        """测试包含新类型的网站解析"""
        from bt_common.utils import parse_all_sites

        sites_data = [
            {"name": "php-site", "status": "1", "stop": "", "_source": "PHP", "ssl": -1},
            {"name": "proxy-site", "status": "1", "healthy": 1, "_source": "Proxy", "ssl": -1, "proxy_pass": "http://example.com"},
            {"name": "html-site", "status": "1", "_source": "HTML", "ssl": -1},
            {"name": "other-site", "status": "1", "project_type": "Other", "_source": "Other", "run": True, "ssl": -1},
        ]

        result = parse_all_sites(sites_data, "test-server")

        assert result["summary"]["total"] == 4
        assert "PHP" in result["summary"]["by_type"]
        assert "Proxy" in result["summary"]["by_type"]
        assert "HTML" in result["summary"]["by_type"]
        assert "Other" in result["summary"]["by_type"]


class TestServiceAPI:
    """测试服务状态API"""

    def test_service_log_paths_defined(self):
        """测试服务日志路径定义"""
        from bt_common.api_endpoints import SERVICE_LOG_PATHS

        assert "nginx" in SERVICE_LOG_PATHS
        assert "apache" in SERVICE_LOG_PATHS
        assert "redis" in SERVICE_LOG_PATHS
        assert SERVICE_LOG_PATHS["nginx"] == "/www/server/nginx/logs/error.log"

    def test_special_service_apis_defined(self):
        """测试特殊服务API定义"""
        from bt_common.api_endpoints import SPECIAL_SERVICE_APIS

        assert "pgsql" in SPECIAL_SERVICE_APIS
        assert "status" in SPECIAL_SERVICE_APIS["pgsql"]
        assert "log" in SPECIAL_SERVICE_APIS["pgsql"]
        assert "slow_log" in SPECIAL_SERVICE_APIS["pgsql"]

    def test_software_services_defined(self):
        """测试软件服务列表定义"""
        from bt_common.api_endpoints import SOFTWARE_SERVICES

        assert "nginx" in SOFTWARE_SERVICES
        assert "apache" in SOFTWARE_SERVICES
        assert "redis" in SOFTWARE_SERVICES
        assert "memcached" in SOFTWARE_SERVICES
        assert "pure-ftpd" in SOFTWARE_SERVICES

    def test_php_versions_defined(self):
        """测试PHP版本列表定义"""
        from bt_common.api_endpoints import PHP_VERSIONS

        assert "8.4" in PHP_VERSIONS
        assert "8.3" in PHP_VERSIONS
        assert "7.4" in PHP_VERSIONS

    def test_new_api_endpoints(self):
        """测试新增API端点"""
        from bt_common.api_endpoints import API_ENDPOINTS

        assert "SOFTWARE_INFO" in API_ENDPOINTS
        assert "SOFTWARE_LIST" in API_ENDPOINTS
        assert "FILE_BODY" in API_ENDPOINTS
        assert API_ENDPOINTS["SOFTWARE_INFO"] == "/plugin?action=get_soft_find"
        assert API_ENDPOINTS["FILE_BODY"] == "/files?action=GetFileBody"

    def test_ssh_api_endpoints(self):
        """测试SSH API端点"""
        from bt_common.api_endpoints import API_ENDPOINTS

        assert "SSH_INFO" in API_ENDPOINTS
        assert "SSH_LOGS" in API_ENDPOINTS
        assert API_ENDPOINTS["SSH_INFO"] == "/safe?action=GetSshInfo"
        assert API_ENDPOINTS["SSH_LOGS"] == "/mod/ssh/com/get_ssh_list"

    def test_crontab_api_endpoints(self):
        """测试计划任务API端点"""
        from bt_common.api_endpoints import API_ENDPOINTS

        assert "CRONTAB_LIST" in API_ENDPOINTS
        assert "CRONTAB_LOGS" in API_ENDPOINTS
        assert API_ENDPOINTS["CRONTAB_LIST"] == "/crontab?action=GetCrontab"
        assert API_ENDPOINTS["CRONTAB_LOGS"] == "/crontab?action=GetLogs"
