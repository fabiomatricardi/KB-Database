"""
Build script for ArticleDatabase.
Creates a standalone Windows .exe using PyInstaller.

Prerequisites:
  1. Build the Vue frontend: cd frontend && npm install && npm run build
  2. Install Python deps: uv sync
  3. Install PyInstaller: uv add --dev pyinstaller
  4. Run this script: uv run python build.py
"""
import subprocess
import sys
import os
import shutil


def main():
    project_root = os.path.dirname(os.path.abspath(__file__))
    frontend_dist = os.path.join(project_root, "frontend", "dist")
    backend_main = os.path.join(project_root, "backend", "main.py")

    if not os.path.isdir(frontend_dist):
        print("ERROR: frontend/dist not found. Build the Vue frontend first:")
        print("  cd frontend && npm install && npm run build")
        sys.exit(1)

    print("=" * 60)
    print("  Building ArticleDatabase .exe")
    print("=" * 60)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--noconsole",
        "--name", "ArticleDatabase-v0.3.3",
        "--add-data", f"frontend{os.pathsep}frontend",
        "--add-data", f"articles{os.pathsep}articles",
        "--add-data", f"articles_db.json{os.pathsep}.",
        "--add-data", f"backend/services/graphify_patcher.py{os.pathsep}backend/services",
        "--hidden-import", "uvicorn.logging",
        "--hidden-import", "uvicorn.loops",
        "--hidden-import", "uvicorn.loops.auto",
        "--hidden-import", "uvicorn.protocols",
        "--hidden-import", "uvicorn.protocols.http",
        "--hidden-import", "uvicorn.protocols.http.auto",
        "--hidden-import", "uvicorn.protocols.websockets",
        "--hidden-import", "uvicorn.protocols.websockets.auto",
        "--hidden-import", "uvicorn.lifespan",
        "--hidden-import", "uvicorn.lifespan.on",
        "--hidden-import", "fastapi",
        "--hidden-import", "starlette",
        "--hidden-import", "pydantic",
        "--hidden-import", "rank_bm25",
        "--hidden-import", "requests",
        "--hidden-import", "anyio",
        "--hidden-import", "anyio._backends",
        "--hidden-import", "anyio._backends._asyncio",
        "--hidden-import", "httpx",
        "--hidden-import", "ddgs",
        "--hidden-import", "bs4",
        "--hidden-import", "bs4.builder",
        "--hidden-import", "lxml",
        "--hidden-import", "lxml.etree",
        "--hidden-import", "lxml.html",
        "--hidden-import", "tavily",
        "--hidden-import", "tavily._client",
        "--hidden-import", "openai",
        "--hidden-import", "openai._client",
        "--collect-all", "uvicorn",
        "--collect-all", "graphify",
        backend_main,
    ]

    print(f"\nRunning: {' '.join(cmd[:6])} ...")
    result = subprocess.run(cmd, cwd=project_root)

    if result.returncode == 0:
        exe_path = os.path.join(project_root, "dist", "ArticleDatabase-v0.3.3.exe")

        # Unblock exe (Windows Smart App Control)
        try:
            subprocess.run(
                ["powershell", "-Command", f"Unblock-File -Path '{exe_path}'"],
                check=False, capture_output=True
            )
            print(f"  Unblocked: {exe_path}")
        except Exception:
            pass  # Non-Windows or PowerShell not available

        print(f"\n{'=' * 60}")
        print(f"  BUILD SUCCESSFUL!")
        print(f"  Output: {exe_path}")
        print(f"{'=' * 60}")
    else:
        print(f"\nBUILD FAILED with exit code {result.returncode}")
        sys.exit(result.returncode)


if __name__ == "__main__":
    main()
