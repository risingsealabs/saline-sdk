#!/usr/bin/env python3
"""
This script fixes the bindings_docstrings issue by ensuring the module exists
and can be imported during documentation building.
"""

import os
import sys
import shutil
from pathlib import Path

def main():
    # Check if the bindings_docstrings.py file exists in the project
    source_file = Path(__file__).parent.parent / "saline_sdk" / "transaction" / "bindings_docstrings.py"
    
    if not source_file.exists():
        print(f"Error: Could not find {source_file}")
        sys.exit(1)
    
    # The target directory is the site-packages directory where the package is installed
    for path in sys.path:
        if 'site-packages' in path or 'dist-packages' in path:
            target_dir = Path(path) / "saline_sdk" / "transaction"
            if target_dir.exists():
                target_file = target_dir / "bindings_docstrings.py"
                
                # Copy the file to the installed package directory
                shutil.copy(source_file, target_file)
                print(f"Copied bindings_docstrings.py to {target_file}")
                return
    
    print("Could not find saline_sdk in site-packages. Make sure the package is installed.")
    sys.exit(1)

if __name__ == "__main__":
    main() 