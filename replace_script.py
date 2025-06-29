#!/usr/bin/env python3
"""
Script to replace 'quantumtgcalls' with 'tgcall' in all Python files
"""

import os
import re

def replace_string_in_file(filepath, old_string, new_string):
    """Replace old_string with new_string in a file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if old_string in content:
            new_content = content.replace(old_string, new_string)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Updated: {filepath}")
            return True
        else:
            print(f"No change needed for: {filepath}")
            return False
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def find_and_replace_in_py_files(root_dir, old_string, new_string):
    """Find all .py files and replace strings"""
    updated_files = []
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith('.py'):
                filepath = os.path.join(dirpath, filename)
                if replace_string_in_file(filepath, old_string, new_string):
                    updated_files.append(filepath)
    
    return updated_files

def main():
    """Main function"""
    # Define the strings to replace
    OLD_STRING = "quantumtgcalls"
    NEW_STRING = "tgcall"
    
    # Define the root directory to start searching from
    ROOT_DIRECTORY = "."  # Current directory
    
    print(f"Replacing '{OLD_STRING}' with '{NEW_STRING}' in all .py files under '{ROOT_DIRECTORY}'...")
    
    updated_files = find_and_replace_in_py_files(ROOT_DIRECTORY, OLD_STRING, NEW_STRING)
    
    print(f"\nReplacement complete. Updated {len(updated_files)} files:")
    for file in updated_files:
        print(f"  - {file}")

if __name__ == "__main__":
    main()