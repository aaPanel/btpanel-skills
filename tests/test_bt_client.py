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

sys.path.insert(0, str(Path(__file__).parent.parent / "skills"))

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
            assert "action=" in endpoint, f"{name} 端点应包含 action 参数"
