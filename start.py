#!/usr/bin/env python3
"""
EduAssistant 一键启动脚本（跨平台：Windows / macOS / Linux）

用法：
    python start.py          # 启动前后端
    python start.py backend  # 仅启动后端
    python start.py frontend # 仅启动前端

Windows 用户也可双击项目根目录下的 start.bat。
"""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"

IS_WIN = sys.platform == "win32"
IS_MAC = sys.platform == "darwin"

# ── ANSI 颜色（Windows 10+ 原生支持） ────────────────────────────
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
CYAN = "\033[0;36m"
NC = "\033[0m"  # reset

_processes: list[subprocess.Popen] = []
_npm_path: str | None = None


# ── 工具函数 ─────────────────────────────────────────────────────
def _venv_python() -> Path:
    """返回 venv 内的 Python 可执行文件路径"""
    if IS_WIN:
        return BACKEND / "venv" / "Scripts" / "python.exe"
    return BACKEND / "venv" / "bin" / "python"


def _run(
    cmd: list[str],
    *,
    cwd: str | Path,
    desc: str = "",
    check: bool = True,
    env: dict[str, str] | None = None,
) -> int:
    """运行命令，实时输出。返回 exit code。"""
    label = f"  [{desc}]" if desc else ""
    print(f"{CYAN}>>> {label} {' '.join(cmd)}{NC}")
    try:
        result = subprocess.run(cmd, cwd=str(cwd), env=env)
    except FileNotFoundError:
        print(f"{RED}未找到命令: {cmd[0]}{NC}")
        print(f"{YELLOW}请确认该命令已安装，并且所在目录已加入 PATH。{NC}")
        sys.exit(1)
    if check and result.returncode != 0:
        print(f"{RED}命令失败 (exit={result.returncode}): {' '.join(cmd)}{NC}")
        sys.exit(result.returncode)
    return result.returncode


def _find_command(command: str) -> str | None:
    """在 PATH 和常见安装目录中查找命令。"""
    found = shutil.which(command)
    if found:
        return found

    common_dirs: list[Path] = []
    if IS_MAC:
        common_dirs.extend([Path("/opt/homebrew/bin"), Path("/usr/local/bin")])
        nvm_dir = Path.home() / ".nvm" / "versions" / "node"
        if nvm_dir.is_dir():
            common_dirs.extend(sorted(nvm_dir.glob("*/bin"), reverse=True))
    elif IS_WIN:
        appdata = os.environ.get("APPDATA")
        program_files = os.environ.get("ProgramFiles")
        if appdata:
            common_dirs.append(Path(appdata) / "npm")
        if program_files:
            common_dirs.append(Path(program_files) / "nodejs")
    else:
        common_dirs.extend([Path("/usr/local/bin"), Path("/usr/bin")])

    for directory in common_dirs:
        candidate = directory / command
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


def _print_node_help() -> None:
    """输出前端工具链缺失时的安装提示。"""
    print(f"{RED}未检测到 npm，无法安装或启动前端依赖。{NC}")
    print(f"{YELLOW}请先安装 Node.js LTS（会自带 npm），然后重新运行 ./start.sh。{NC}")
    if IS_MAC:
        print(f"{YELLOW}macOS 可选方式：brew install node，或从 https://nodejs.org/ 下载 LTS 版本。{NC}")
    elif IS_WIN:
        print(f"{YELLOW}Windows 请从 https://nodejs.org/ 下载 LTS 版本，安装后重新打开终端。{NC}")
    else:
        print(f"{YELLOW}Linux 可使用系统包管理器安装 nodejs/npm，或从 https://nodejs.org/ 下载。{NC}")
    print(f"{YELLOW}安装后可用 npm --version 验证。{NC}")


def _npm_cmd() -> str:
    """返回当前平台上的 npm 命令名"""
    global _npm_path
    if _npm_path:
        return _npm_path

    candidates = ["npm.cmd", "npm"] if IS_WIN else ["npm"]
    for command in candidates:
        found = _find_command(command)
        if found:
            _npm_path = found
            return found
    _print_node_help()
    sys.exit(1)


def _env_with_tool_dir(command: str) -> dict[str, str]:
    """确保通过常见路径发现的工具目录也能被其子进程使用。"""
    env = os.environ.copy()
    tool_dir = str(Path(command).resolve().parent)
    current_path = env.get("PATH", "")
    if tool_dir and tool_dir not in current_path.split(os.pathsep):
        env["PATH"] = tool_dir + os.pathsep + current_path
    return env


# ── 后端 ──────────────────────────────────────────────────────────
def setup_backend() -> None:
    """创建 venv、安装依赖、复制 .env"""
    print(f"\n{CYAN}{'─' * 50}{NC}")
    print(f"{CYAN}  准备后端环境{NC}")
    print(f"{CYAN}{'─' * 50}{NC}")

    os.chdir(BACKEND)

    # 1. 创建虚拟环境
    venv_dir = BACKEND / "venv"
    if not venv_dir.is_dir():
        print(f"{YELLOW}  创建 Python 虚拟环境...{NC}")
        _run([sys.executable, "-m", "venv", str(venv_dir)], cwd=BACKEND, desc="venv")

    python = str(_venv_python())

    # 2. 安装依赖
    try:
        subprocess.run(
            [python, "-c", "import fastapi"], capture_output=True, check=True
        )
    except subprocess.CalledProcessError:
        print(f"{YELLOW}  安装后端依赖（首次可能较慢）...{NC}")
        _run(
            [python, "-m", "pip", "install", "-r", "requirements.txt", "-q"],
            cwd=BACKEND,
            desc="pip install",
        )

    # 3. .env
    env_file = BACKEND / ".env"
    if not env_file.exists():
        example = BACKEND / ".env.example"
        if example.exists():
            shutil.copy(example, env_file)
            print(f"{YELLOW}  .env 未找到，已从 .env.example 复制，请编辑填入 API Key{NC}")
        else:
            print(f"{RED}  缺少 .env.example，请手动创建 .env 文件{NC}")


def start_backend() -> subprocess.Popen:
    """启动后端 uvicorn，返回进程对象"""
    python = str(_venv_python())
    print(f"{GREEN}  后端启动中 → http://localhost:8000{NC}")
    print(f"{GREEN}  API 文档  → http://localhost:8000/docs{NC}")

    proc = subprocess.Popen(
        [python, "-m", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
        cwd=str(BACKEND),
    )
    _processes.append(proc)
    return proc


# ── 前端 ──────────────────────────────────────────────────────────
def setup_frontend() -> None:
    """安装 npm 依赖"""
    print(f"\n{CYAN}{'─' * 50}{NC}")
    print(f"{CYAN}  准备前端环境{NC}")
    print(f"{CYAN}{'─' * 50}{NC}")

    os.chdir(FRONTEND)

    if not (FRONTEND / "node_modules").is_dir():
        print(f"{YELLOW}  安装前端依赖（首次可能较慢）...{NC}")
        npm = _npm_cmd()
        _run([npm, "install"], cwd=FRONTEND, desc="npm install", env=_env_with_tool_dir(npm))


def start_frontend() -> subprocess.Popen:
    """启动前端 dev server"""
    print(f"{GREEN}  前端启动中 → http://localhost:5173{NC}")
    npm = _npm_cmd()

    proc = subprocess.Popen(
        [npm, "run", "dev"], cwd=str(FRONTEND), env=_env_with_tool_dir(npm),
    )
    _processes.append(proc)
    return proc


# ── 清理 ──────────────────────────────────────────────────────────
def cleanup() -> None:
    """关闭所有子进程"""
    if not _processes:
        return
    print(f"\n{YELLOW}  正在关闭服务...{NC}")
    for proc in _processes:
        try:
            proc.terminate()
        except Exception:
            pass
    # 等待最多 5 秒
    deadline = time.time() + 5
    for proc in _processes:
        timeout = max(0, deadline - time.time())
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            try:
                proc.kill()
            except Exception:
                pass
    _processes.clear()
    print(f"{GREEN}  服务已关闭{NC}")


def _sig_handler(signum: int, frame: object) -> None:
    """信号处理"""
    cleanup()
    sys.exit(0)


# ── 主入口 ────────────────────────────────────────────────────────
def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"

    print(f"\n{GREEN}  ╔{'═' * 46}╗{NC}")
    print(f"{GREEN}  ║{'EduAssistant 一键启动':^38}║{NC}")
    print(f"{GREEN}  ║{f'平台: {sys.platform}':^38}║{NC}")
    print(f"{GREEN}  ╚{'═' * 46}╝{NC}")

    if mode not in ("all", "backend", "frontend"):
        print(f"{RED}用法: python start.py [all|backend|frontend]{NC}")
        sys.exit(1)

    if mode in ("all", "frontend"):
        _npm_cmd()

    # 注册清理
    signal.signal(signal.SIGINT, _sig_handler)
    signal.signal(signal.SIGTERM, _sig_handler)

    if mode in ("all", "backend"):
        setup_backend()

    if mode in ("all", "frontend"):
        setup_frontend()

    print(f"\n{GREEN}{'─' * 50}{NC}")

    if mode in ("all", "backend"):
        start_backend()

    if mode in ("all", "frontend"):
        start_frontend()

    print(f"\n{GREEN}  ╔{'═' * 46}╗{NC}")
    print(f"{GREEN}  ║{'启动完成！按 Ctrl+C 停止所有服务':^36}║{NC}")
    print(f"{GREEN}  ╠{'═' * 46}╣{NC}")
    if mode in ("all", "frontend"):
        print(f"{GREEN}  ║  前端: http://localhost:5173{'':19}║{NC}")
    if mode in ("all", "backend"):
        print(f"{GREEN}  ║  后端: http://localhost:8000{'':19}║{NC}")
        print(f"{GREEN}  ║  API:  http://localhost:8000/docs{'':15}║{NC}")
    print(f"{GREEN}  ╚{'═' * 46}╝{NC}\n")

    try:
        for proc in _processes:
            proc.wait()
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()


if __name__ == "__main__":
    main()
