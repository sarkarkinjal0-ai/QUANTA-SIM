"""
QUANTA-SIM: Quantum Circuit Framework
Shortcut runner within qiskitintegration package.
"""
from pathlib import Path
import sys

# Forward execution to root run_demo
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from run_demo import main

if __name__ == "__main__":
    main()
