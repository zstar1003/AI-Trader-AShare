"""
项目状态检查脚本
检查项目配置和数据文件的完整性
"""
import os
import json
from pathlib import Path

def check_file_exists(filepath, description):
    """检查文件是否存在"""
    exists = os.path.exists(filepath)
    status = "[OK]" if exists else "[FAIL]"
    print(f"{status} {description}: {filepath}")
    return exists

def check_json_valid(filepath):
    """检查JSON文件是否有效"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            json.load(f)
        print(f"  [OK] JSON format is valid")
        return True
    except Exception as e:
        print(f"  [FAIL] JSON format error: {e}")
        return False

def main():
    print("=" * 60)
    print("AI-Trader A股 项目状态检查")
    print("=" * 60)

    base_dir = Path(__file__).parent.parent
    all_ok = True

    # 1. 检查必要的配置文件
    print("\n[1] 配置文件检查")
    print("-" * 60)

    files_to_check = [
        (".env", "环境变量文件"),
        (".env.example", "环境变量示例"),
        ("pyproject.toml", "项目配置"),
        (".gitignore", "Git忽略配置"),
        ("README.md", "项目说明"),
        ("DEPLOYMENT.md", "部署指南"),
    ]

    for file, desc in files_to_check:
        filepath = base_dir / file
        if not check_file_exists(filepath, desc):
            all_ok = False

    # 2. 检查前端文件
    print("\n[2] 前端文件检查")
    print("-" * 60)

    frontend_files = [
        ("docs/index.html", "主页面"),
        ("docs/css/style.css", "样式文件"),
        ("docs/js/main.js", "JavaScript文件"),
    ]

    for file, desc in frontend_files:
        filepath = base_dir / file
        if not check_file_exists(filepath, desc):
            all_ok = False

    # 3. 检查脚本文件
    print("\n[3] 数据脚本检查")
    print("-" * 60)

    script_files = [
        ("scripts/fetch_market_data.py", "数据获取脚本"),
    ]

    for file, desc in script_files:
        filepath = base_dir / file
        if not check_file_exists(filepath, desc):
            all_ok = False

    # 4. 检查GitHub Actions配置
    print("\n[4] GitHub Actions 配置检查")
    print("-" * 60)

    workflow_files = [
        (".github/workflows/update-data.yml", "数据更新工作流"),
        (".github/workflows/deploy.yml", "部署工作流"),
    ]

    for file, desc in workflow_files:
        filepath = base_dir / file
        if not check_file_exists(filepath, desc):
            all_ok = False

    # 5. 检查数据文件
    print("\n[5] 数据文件检查")
    print("-" * 60)

    data_dir = base_dir / "docs" / "data"
    if check_file_exists(data_dir, "数据目录"):
        data_files = [
            ("summary.json", "汇总信息"),
            ("indices.json", "指数数据"),
            ("stocks.json", "股票数据"),
        ]

        for file, desc in data_files:
            filepath = data_dir / file
            if check_file_exists(filepath, desc):
                check_json_valid(filepath)
            else:
                all_ok = False
                print(f"  [WARN] Data files missing, please run: python scripts/fetch_market_data.py")
    else:
        all_ok = False

    # 6. 检查环境变量
    print("\n[6] 环境变量检查")
    print("-" * 60)

    env_file = base_dir / ".env"
    if env_file.exists():
        try:
            with open(env_file, 'r') as f:
                content = f.read()
                has_token = 'TUSHARE_API_KEY' in content and 'your_' not in content
                if has_token:
                    print("[OK] TUSHARE_API_KEY configured")
                else:
                    print("[FAIL] TUSHARE_API_KEY not configured or using example value")
                    print("  Please fill in real Tushare Token in .env file")
                    all_ok = False
        except Exception as e:
            print(f"[FAIL] Failed to read environment variables: {e}")
            all_ok = False
    else:
        print("[FAIL] .env file does not exist")
        print("  Please copy .env.example to .env and configure your Token")
        all_ok = False

    # 总结
    print("\n" + "=" * 60)
    if all_ok:
        print("[OK] All checks passed! Project configuration is complete")
        print("\nNext steps:")
        print("1. Local test: python scripts/fetch_market_data.py")
        print("2. Local preview: cd docs && python -m http.server 8000")
        print("3. Push to GitHub and configure GitHub Pages")
    else:
        print("[FAIL] Issues found, please fix according to above prompts")
    print("=" * 60)

if __name__ == '__main__':
    main()
