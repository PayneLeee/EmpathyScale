"""
Run all three core experiments in sequence:
1. run_predefined_scenarios.py - Main scale generation
2. run_ablation_minimal.py - Ablation study
3. run_baseline_comparison.py - Baseline comparison

This script handles errors and provides progress tracking.
"""

import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def print_header(text: str, char: str = "="):
    """Print a formatted header."""
    width = 80
    print(f"\n{char * width}")
    print(f"{text:^{width}}")
    print(f"{char * width}\n")


def print_step(step_num: int, total_steps: int, description: str):
    """Print a step indicator."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{step_num}/{total_steps}] {description}...")


def print_success(message: str):
    """Print a success message."""
    print(f"[OK] {message}")


def print_error(message: str):
    """Print an error message."""
    print(f"[ERROR] {message}")


def print_warning(message: str):
    """Print a warning message."""
    print(f"[WARN] {message}")


def check_prerequisites():
    """Check if prerequisites are met."""
    print_header("CHECKING PREREQUISITES", "=")
    
    # Check config.json
    config_path = project_root / "config.json"
    if not config_path.exists():
        print_error("config.json not found!")
        print_warning("Please create config.json with your OpenAI API key:")
        print_warning('  {"openai_api_key": "your-key-here"}')
        return False
    
    try:
        import json
        config = json.loads(config_path.read_text(encoding="utf-8"))
        if not config.get("openai_api_key"):
            print_error("openai_api_key not found in config.json")
            return False
        print_success("config.json found and valid")
    except Exception as e:
        print_error(f"Error reading config.json: {e}")
        return False
    
    # Check Python version
    if sys.version_info < (3, 8):
        print_error(f"Python 3.8+ required, found {sys.version}")
        return False
    print_success(f"Python version: {sys.version.split()[0]}")
    
    # Check required files exist
    required_files = [
        "run_predefined_scenarios.py",
        "run_ablation_minimal.py",
        "run_baseline_comparison.py"
    ]
    
    for file in required_files:
        file_path = project_root / file
        if not file_path.exists():
            print_error(f"Required file not found: {file}")
            return False
        print_success(f"Found: {file}")
    
    print()
    return True


def run_script(script_name: str, step_num: int, total_steps: int):
    """Run a Python script and handle errors."""
    print_step(step_num, total_steps, f"Running {script_name}")
    print(f"  Command: python {script_name}")
    print(f"  Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    script_path = project_root / script_name
    
    try:
        # Run the script
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(project_root),
            capture_output=False,  # Show output in real-time
            text=True,
            check=False  # Don't raise exception on non-zero exit
        )
        
        if result.returncode == 0:
            print()
            print_success(f"{script_name} completed successfully")
            print(f"  End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            return True
        else:
            print()
            print_error(f"{script_name} failed with exit code {result.returncode}")
            return False
            
    except KeyboardInterrupt:
        print()
        print_warning(f"{script_name} interrupted by user")
        return False
    except Exception as e:
        print()
        print_error(f"Error running {script_name}: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function to run all experiments."""
    print_header("RUNNING ALL EXPERIMENTS", "=")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check prerequisites
    if not check_prerequisites():
        print_error("Prerequisites check failed. Please fix the issues above.")
        sys.exit(1)
    
    # Define experiments in order
    experiments = [
        ("run_predefined_scenarios.py", "Main Scale Generation (3 scenarios)"),
        ("run_ablation_minimal.py", "Ablation Study (4 variants)"),
        ("run_baseline_comparison.py", "Baseline Comparison (PETS & RoPE)")
    ]
    
    results = []
    
    # Run each experiment
    for idx, (script_name, description) in enumerate(experiments, 1):
        print_header(f"EXPERIMENT {idx}: {description.upper()}", "-")
        
        success = run_script(script_name, idx, len(experiments))
        results.append((script_name, success))
        
        if not success:
            print_warning(f"Experiment {idx} failed. Continuing with next experiment...")
            print_warning("You can re-run failed experiments individually later.")
        
        print()
    
    # Summary
    print_header("EXPERIMENTS SUMMARY", "=")
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    for idx, (script_name, success) in enumerate(results, 1):
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"  [{idx}] {script_name}: {status}")
    
    print()
    
    # Final status
    all_success = all(success for _, success in results)
    if all_success:
        print_success("All experiments completed successfully!")
    else:
        failed = [name for name, success in results if not success]
        print_warning(f"Some experiments failed: {', '.join(failed)}")
        print_warning("Please check the output above for error details.")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_warning("Experiments interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


