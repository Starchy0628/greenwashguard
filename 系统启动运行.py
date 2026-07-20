#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GreenwashGuard - 静默启动管理器（无日志版本）
- 自动检查Python依赖（缺失则安装）
- 自动检查.env配置文件
- 后台启动uvicorn服务器（无控制台窗口）
- 等待服务就绪后自动打开浏览器
"""
import os
import sys
import subprocess
import time
import socket
import importlib
from pathlib import Path

ROOT_DIR = Path(__file__).parent.absolute()
BACKEND_DIR = ROOT_DIR / "backend"
PORT = 8000


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return False
        except OSError:
            return True


def wait_for_service(port: int, timeout: int = 45) -> bool:
    """等待HTTP服务就绪"""
    start = time.time()
    while time.time() - start < timeout:
        if is_port_in_use(port):
            try:
                import urllib.request
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=3) as resp:
                    if resp.status == 200:
                        return True
            except Exception:
                pass
        time.sleep(1)
    return False


def check_package(pkg_name: str) -> bool:
    try:
        importlib.import_module(pkg_name)
        return True
    except ImportError:
        return False


def install_requirements():
    """检查并安装Python依赖"""
    req_file = BACKEND_DIR / "requirements.txt"
    if not req_file.exists():
        return True

    # 检查关键包
    critical = {
        "fastapi": "fastapi",
        "uvicorn": "uvicorn",
        "sqlalchemy": "sqlalchemy",
        "pydantic": "pydantic",
        "fitz": "PyMuPDF",
        "pdfplumber": "pdfplumber",
    }

    missing = []
    for import_name, pkg_name in critical.items():
        if not check_package(import_name):
            missing.append(pkg_name)

    if missing:
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
                cwd=str(BACKEND_DIR),
                check=True,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            )
        except subprocess.CalledProcessError:
            return False
    return True


def ensure_env_file():
    """确保.env文件存在"""
    env_file = BACKEND_DIR / ".env"
    env_example = BACKEND_DIR / ".env.example"
    if not env_file.exists() and env_example.exists():
        import shutil
        shutil.copy(env_example, env_file)
    return True


def start_server():
    """启动uvicorn服务器（后台，无窗口）"""
    if is_port_in_use(PORT):
        # 端口已占用，服务可能已在运行
        return True

    # 使用pythonw.exe启动（无控制台窗口）
    python_exe = sys.executable
    if python_exe.endswith("python.exe") and os.name == "nt":
        pythonw = python_exe.replace("python.exe", "pythonw.exe")
        if os.path.exists(pythonw):
            python_exe = pythonw

    startupinfo = None
    creationflags = 0
    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0
        creationflags = subprocess.CREATE_NO_WINDOW

    cmd = [
        python_exe, "-m", "uvicorn",
        "app.main:app",
        "--host", "127.0.0.1",
        "--port", str(PORT),
    ]

    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(BACKEND_DIR),
            startupinfo=startupinfo,
            creationflags=creationflags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return wait_for_service(PORT, timeout=45)
    except Exception:
        return False


def open_browser():
    """打开默认浏览器"""
    url = f"http://localhost:{PORT}"
    try:
        if os.name == "nt":
            os.startfile(url)
        elif sys.platform == "darwin":
            subprocess.run(["open", url])
        else:
            subprocess.run(["xdg-open", url])
    except Exception:
        pass


def main():
    os.chdir(str(ROOT_DIR))

    if not ensure_env_file():
        return
    if not install_requirements():
        return
    if start_server():
        # 延迟打开浏览器，确保前端页面加载
        time.sleep(3)
        open_browser()


if __name__ == "__main__":
    main()
