"""
将agent数据复制到docs目录以便本地预览
"""
import shutil
import os
from pathlib import Path

# 项目根目录
root_dir = Path(__file__).parent.parent
data_source = root_dir / "data" / "agent_data"
data_dest = root_dir / "docs" / "data"

# 确保目标目录存在
data_dest.mkdir(parents=True, exist_ok=True)

# 复制所有agent数据文件
if data_source.exists():
    for file in data_source.glob("*_state.json"):
        dest_file = data_dest / file.name
        shutil.copy2(file, dest_file)
        print(f"[OK] Copy: {file.name} -> {dest_file}")
    print(f"\n[SUCCESS] Data copied to {data_dest}")
else:
    print(f"[ERROR] Source directory not found: {data_source}")
    print("Please run: python run_simulation.py")
