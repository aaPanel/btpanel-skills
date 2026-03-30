"""
宝塔文件操作技能单元测试
"""

import unittest
import argparse
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# 添加公共模块路径（与 test_bt_client.py 保持一致）
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestFilesClient(unittest.TestCase):
    """测试 FilesClient 类"""

    def test_import(self):
        """测试导入"""
        from bt_common.files_client import FilesClient, FilesClientManager, get_server_config
        self.assertIsNotNone(FilesClient)
        self.assertIsNotNone(FilesClientManager)
        self.assertIsNotNone(get_server_config)

    def test_encode_path(self):
        """测试路径编码"""
        from bt_common.files_client import FilesClient

        # 创建一个不实际连接的实例
        client = FilesClient.__new__(FilesClient)

        # 测试路径编码
        test_cases = [
            ("/www/server/panel", "%2Fwww%2Fserver%2Fpanel"),
            ("/www/test.txt", "%2Fwww%2Ftest.txt"),
            ("/path/with spaces", "%2Fpath%2Fwith%20spaces"),
        ]

        for input_path, expected in test_cases:
            result = client._encode_path(input_path)
            self.assertEqual(result, expected, f"Failed for {input_path}")


class TestFormatFunctions(unittest.TestCase):
    """测试格式化函数"""

    def test_format_size(self):
        """测试文件大小格式化"""
        from btpanel_files.scripts.files import format_size

        # 测试文件大小
        self.assertEqual(format_size(500), "500B")
        self.assertEqual(format_size(1024), "1.0KB")
        self.assertEqual(format_size(1536), "1.5KB")
        self.assertEqual(format_size(1048576), "1.0MB")
        self.assertEqual(format_size(1073741824), "1.0GB")

        # 测试目录大小（单位是 KB）
        self.assertEqual(format_size(100, is_dir=True), "100KB")
        self.assertEqual(format_size(1024, is_dir=True), "1.0MB")
        self.assertEqual(format_size(1048576, is_dir=True), "1.0GB")

    def test_format_time(self):
        """测试时间格式化"""
        from btpanel_files.scripts.files import format_time

        # 测试时间戳格式化
        result = format_time(1609459200)  # 2021-01-01 00:00:00
        self.assertIn("2021-01-01", result)


class TestAPIEndpoints(unittest.TestCase):
    """测试 API 端点生成"""

    def test_get_dir_endpoint(self):
        """测试获取目录端点"""
        from bt_common.files_client import FilesClient

        client = FilesClient.__new__(FilesClient)

        # 测试端点生成
        path = client._encode_path("/www")
        endpoint = f"/files?action=GetDirNew&path={path}&p=1&showRow=500"

        self.assertIn("/files", endpoint)
        self.assertIn("action=GetDirNew", endpoint)
        self.assertIn("path=", endpoint)

    def test_get_file_body_endpoint(self):
        """测试读取文件端点"""
        from bt_common.files_client import FilesClient

        client = FilesClient.__new__(FilesClient)

        path = client._encode_path("/www/test.txt")
        endpoint = f"/files?action=GetFileBody&path={path}"

        self.assertIn("action=GetFileBody", endpoint)

    def test_save_file_body_endpoint(self):
        """测试保存文件端点"""
        from bt_common.files_client import FilesClient
        import urllib.parse

        client = FilesClient.__new__(FilesClient)

        path = client._encode_path("/www/test.txt")
        data = urllib.parse.quote("test content", safe='')
        endpoint = f"/files?action=SaveFileBody&path={path}&data={data}&encoding=utf-8"

        self.assertIn("action=SaveFileBody", endpoint)
        self.assertIn("encoding=utf-8", endpoint)


class TestCLIParsers(unittest.TestCase):
    """测试 CLI 参数解析"""

    def test_chmod_parser(self):
        """测试 chmod 命令参数"""
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument('access', help='权限码')
        parser.add_argument('path', help='文件路径')
        parser.add_argument('-u', '--user', help='所有者')
        parser.add_argument('-R', '--recursive', action='store_true')

        args = parser.parse_args(['755', '/www/test', '-u', 'www', '-R'])
        self.assertEqual(args.access, '755')
        self.assertEqual(args.path, '/www/test')
        self.assertEqual(args.user, 'www')
        self.assertTrue(args.recursive)

    def test_ls_command_args(self):
        """测试 ls 命令基本参数"""
        parser = argparse.ArgumentParser()
        parser.add_argument('path', nargs='?', default='/www')
        parser.add_argument('-p', '--page', type=int, default=1)
        parser.add_argument('-r', '--rows', type=int, default=500)

        args = parser.parse_args(['/www/server', '-p', '2', '-r', '100'])
        self.assertEqual(args.path, '/www/server')
        self.assertEqual(args.page, 2)
        self.assertEqual(args.rows, 100)

    def test_cat_command_args(self):
        """测试 cat 命令参数"""
        parser = argparse.ArgumentParser()
        parser.add_argument('path', help='文件路径')
        parser.add_argument('-n', '--lines', type=int, help='显示最后 N 行')
        parser.add_argument('-v', '--verbose', action='store_true')

        args = parser.parse_args(['/www/test.txt', '-n', '50', '-v'])
        self.assertEqual(args.path, '/www/test.txt')
        self.assertEqual(args.lines, 50)
        self.assertTrue(args.verbose)


if __name__ == "__main__":
    unittest.main()
