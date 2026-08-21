#!/usr/bin/env python3
"""Download, verify, and run the official Baota MCP setup entrypoint.

The installer shell script is intentionally not bundled in this Skill. It is
downloaded over verified HTTPS into a private temporary file, checked against
the pinned SHA-256 below, and executed without shell command interpolation.
"""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import shlex
import ssl
import stat
import subprocess
import sys
import tempfile
import urllib.request


INSTALLER_URL = "https://download.bt.cn/bt_mcp_install/btw_mcp_setup.sh"
INSTALLER_SHA256 = "96995754c50170d0bf4bc8fe93a29dd342b4f00c5d3d0607fcc943d03b8457ab"
TLS_GUIDE_URL = (
    "https://docs.bt.cn/user-guide/ai/mcp-installation#申请可信-ip-证书"
)
RESULT_START = "===BTW_RESULT_START==="
RESULT_END = "===BTW_RESULT_END==="
MAX_INSTALLER_BYTES = 2 * 1024 * 1024
SECRET_VALUE_PATTERN = re.compile(
    r"(?i)(token|password|passwd|api[ _-]?key|authorization)(\s*[:=]\s*)(\S+)"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="安全下载并执行宝塔 MCP 官方安装入口"
    )
    parser.add_argument(
        "--target",
        help="远程 SSH 目标，如 root@1.2.3.4；省略时在本机执行",
    )
    parser.add_argument("--ssh-port", type=int, default=22)
    parser.add_argument(
        "--allow-ips",
        default="127.0.0.1",
        help="MCP 来源白名单，多个 IP/CIDR 用逗号分隔；禁止 *",
    )
    parser.add_argument(
        "--mcp-host",
        help="MCP 对外地址；远程模式默认取 SSH 目标主机，本机默认 127.0.0.1",
    )
    parser.add_argument("--auto-upgrade", action="store_true")
    parser.add_argument(
        "--result-file",
        type=Path,
        required=True,
        help="保存完整结构化结果的本地文件；权限会设置为 0600",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="确认执行；仅在 Agent 已向用户说明影响并取得确认后使用",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> str:
    if not 1 <= args.ssh_port <= 65535:
        raise ValueError("SSH 端口必须在 1-65535 之间")

    allow_items = [item.strip() for item in args.allow_ips.split(",") if item.strip()]
    if not allow_items or "*" in allow_items:
        raise ValueError("白名单必须包含明确的 IP/CIDR，不能使用 *")
    for item in allow_items:
        try:
            ipaddress.ip_network(item, strict=False)
        except ValueError as exc:
            raise ValueError(f"无效白名单项: {item}") from exc

    if args.mcp_host:
        mcp_host = args.mcp_host
    elif args.target:
        mcp_host = args.target.rsplit("@", 1)[-1].strip("[]")
    else:
        mcp_host = "127.0.0.1"

    if not mcp_host or re.search(r"[\s/;&|`$]", mcp_host):
        raise ValueError("MCP host 包含不允许的字符")
    return mcp_host


def download_installer() -> tuple[Path, str]:
    request = urllib.request.Request(
        INSTALLER_URL,
        headers={"User-Agent": "btpanel-skill-installer/1.0"},
    )
    tls_context = ssl.create_default_context()
    if ssl.get_default_verify_paths().cafile is None:
        try:
            import certifi
        except ImportError:
            pass
        else:
            tls_context = ssl.create_default_context(cafile=certifi.where())

    with urllib.request.urlopen(
        request, timeout=30, context=tls_context
    ) as response:
        final_url = response.geturl()
        if not final_url.startswith("https://"):
            raise RuntimeError(f"安装入口重定向到非 HTTPS 地址: {final_url}")
        data = response.read(MAX_INSTALLER_BYTES + 1)

    if len(data) > MAX_INSTALLER_BYTES:
        raise RuntimeError("安装入口大小异常，拒绝执行")
    if not data.startswith(b"#!/bin/bash"):
        raise RuntimeError("安装入口格式异常，缺少预期 shebang")

    actual_hash = hashlib.sha256(data).hexdigest()
    if actual_hash != INSTALLER_SHA256:
        raise RuntimeError(
            "安装入口 SHA-256 不匹配；请审查官方更新并刷新 Skill，"
            f"expected={INSTALLER_SHA256}, actual={actual_hash}"
        )

    fd, raw_path = tempfile.mkstemp(prefix="btw-mcp-setup-", suffix=".sh")
    path = Path(raw_path)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
        path.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return path, actual_hash


def installer_args(args: argparse.Namespace, mcp_host: str) -> list[str]:
    values = ["--allow-ips", args.allow_ips]
    if mcp_host != "127.0.0.1":
        values.extend(["--mcp-host", mcp_host])
    if args.auto_upgrade:
        values.append("--auto-upgrade")
    return values


def run_installer(
    path: Path, args: argparse.Namespace, mcp_host: str
) -> subprocess.CompletedProcess[bytes]:
    values = installer_args(args, mcp_host)
    if args.target:
        remote_command = "bash -s -- " + " ".join(shlex.quote(v) for v in values)
        command = [
            "ssh",
            "-o",
            "StrictHostKeyChecking=accept-new",
            "-o",
            "ConnectTimeout=10",
            "-p",
            str(args.ssh_port),
            args.target,
            remote_command,
        ]
        return subprocess.run(
            command,
            input=path.read_bytes(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    command = ["bash", str(path), *values]
    return subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def sanitize_installer_stderr(output: bytes) -> str:
    text = output.decode("utf-8", errors="replace")
    return SECRET_VALUE_PATTERN.sub(r"\1\2[REDACTED]", text)


def extract_result(output: bytes) -> dict:
    text = output.decode("utf-8", errors="replace")
    start = text.rfind(RESULT_START)
    end = text.rfind(RESULT_END)
    if start < 0 or end < 0 or end <= start:
        raise RuntimeError("安装器未返回结构化结果")
    payload = text[start + len(RESULT_START) : end].strip()
    result = json.loads(payload)
    if not isinstance(result, dict):
        raise RuntimeError("安装器结果不是 JSON 对象")
    return result


def classify_binding(result: dict, mcp_host: str) -> None:
    result["installer_source"] = INSTALLER_URL
    result["installer_sha256"] = INSTALLER_SHA256
    result["tls_guide_url"] = TLS_GUIDE_URL

    public_mode = mcp_host not in {"127.0.0.1", "::1", "localhost"}
    candidates = [
        result.get("mcp_url"),
        result.get("local_host"),
        result.get("public_host"),
    ]
    has_https = any(
        isinstance(value, str) and value.startswith("https://") for value in candidates
    )
    cert_problem = (
        result.get("tls_san_matches") is False
        or result.get("tls_self_signed") is True
        or (public_mode and not has_https)
    )
    result["binding_status"] = "blocked_tls" if cert_problem else "ready"
    result["needs_trusted_ip_certificate"] = cert_problem


def write_result(path: Path, result: dict) -> None:
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    except Exception:
        os.close(fd)
        raise


def main() -> int:
    args = parse_args()
    try:
        mcp_host = validate_args(args)
    except ValueError as exc:
        print(f"参数错误: {exc}", file=sys.stderr)
        return 2

    values = installer_args(args, mcp_host)
    target = args.target or "本机"
    print(f"目标: {target}", file=sys.stderr)
    print(f"官方安装入口: {INSTALLER_URL}", file=sys.stderr)
    print(f"固定 SHA-256: {INSTALLER_SHA256}", file=sys.stderr)
    print("安装参数: " + " ".join(shlex.quote(v) for v in values), file=sys.stderr)

    if args.dry_run:
        print(json.dumps({"status": "dry-run", "target": target}, ensure_ascii=False))
        return 0
    if not args.yes:
        answer = input("将以 root 权限安装或升级宝塔面板与 MCP，确认执行？[y/N] ")
        if answer.strip().lower() not in {"y", "yes"}:
            print("已取消", file=sys.stderr)
            return 2

    installer_path: Path | None = None
    try:
        installer_path, actual_hash = download_installer()
        print(f"安装入口校验通过: {actual_hash[:16]}...", file=sys.stderr)
        completed = run_installer(installer_path, args, mcp_host)
        sanitized_stderr = sanitize_installer_stderr(completed.stderr)
        if sanitized_stderr:
            print(sanitized_stderr, file=sys.stderr, end="")
        result = extract_result(completed.stdout)
        classify_binding(result, mcp_host)
        write_result(args.result_file, result)

        summary = {
            "status": result.get("status", "error"),
            "binding_status": result.get("binding_status"),
            "result_file": str(args.result_file.expanduser().resolve()),
            "tls_guide_url": TLS_GUIDE_URL
            if result.get("needs_trusted_ip_certificate")
            else None,
        }
        print(json.dumps(summary, ensure_ascii=False))
        if completed.returncode != 0 or result.get("status") != "ok":
            return 1
        return 0
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(f"安装失败: {exc}", file=sys.stderr)
        return 1
    finally:
        if installer_path is not None:
            installer_path.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
