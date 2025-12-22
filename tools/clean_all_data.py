"""
清理所有历史运行数据

Usage:
    python tools/clean_all_data.py
    or
    python clean_all_data.py (if run from project root)
"""
import shutil
from pathlib import Path

def main():
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    
    print("开始清理所有历史数据...\n")
    
    # 清理 runs 目录
    runs_dir = data_dir / "runs"
    if runs_dir.exists():
        deleted_count = 0
        for run_dir in runs_dir.iterdir():
            if run_dir.is_dir():
                print(f"  删除运行目录: {run_dir.name}")
                shutil.rmtree(run_dir)
                deleted_count += 1
        if deleted_count > 0:
            print(f"  [OK] 已删除 {deleted_count} 个运行目录")
        else:
            print(f"  [OK] data/runs/ 目录为空")
    
    # 清理 test_runs 目录
    test_runs_dir = data_dir / "test_runs"
    if test_runs_dir.exists():
        deleted_count = 0
        for test_run_dir in test_runs_dir.iterdir():
            if test_run_dir.is_dir():
                print(f"  删除测试运行目录: {test_run_dir.name}")
                shutil.rmtree(test_run_dir)
                deleted_count += 1
        if deleted_count > 0:
            print(f"  [OK] 已删除 {deleted_count} 个测试运行目录")
        else:
            print(f"  [OK] data/test_runs/ 目录为空")
    
    # 删除 latest_run.txt
    latest_run_file = data_dir / "latest_run.txt"
    if latest_run_file.exists():
        latest_run_file.unlink()
        print(f"  [OK] 已删除 data/latest_run.txt")
    
    # 清理 personas 目录（递归删除所有子目录）
    personas_dir = data_dir / "personas"
    if personas_dir.exists():
        deleted_count = 0
        for persona_item in personas_dir.iterdir():
            if persona_item.is_dir():
                print(f"  删除persona目录: {persona_item.name}")
                shutil.rmtree(persona_item)
                deleted_count += 1
            elif persona_item.is_file():
                print(f"  删除persona文件: {persona_item.name}")
                persona_item.unlink()
                deleted_count += 1
        if deleted_count > 0:
            print(f"  [OK] 已删除 {deleted_count} 个persona目录/文件")
        else:
            print(f"  [OK] data/personas/ 目录为空")
    
    print("\n" + "="*60)
    print("所有历史数据已清理完成！")
    print("="*60)

if __name__ == "__main__":
    main()
