#!/usr/bin/env python3
import os
import shutil
import tarfile
import glob
import re

# --- Configuration ---
APP_NAME = "marklin-bridge"

# --- Path Configuration ---
# This script determines paths based on its own location, so it can be run from anywhere.
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
# The source root is the parent directory of this script's directory (e.g., '.../pi/opt/marklin-bridge/')
SOURCE_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
# The build will happen in a 'build' subdirectory of the source root.
BUILD_DIR = os.path.join(SOURCE_ROOT, "build")
PACKAGE_DIR = os.path.join(BUILD_DIR, APP_NAME)

# --- Version Extraction ---
# Read the version from constants.py to ensure a single source of truth.
VERSION = "0.0.0-dev" # Default fallback version
try:
    constants_path = os.path.join(SOURCE_ROOT, 'constants.py')
    with open(constants_path, 'r') as f:
        content = f.read()
        match = re.search(r"^APP_VERSION\s*=\s*['\"]([^'\"]*)['\"]", content, re.M)
        if match:
            VERSION = match.group(1)
except Exception as e:
    print(f"Warning: Could not read version from constants.py: {e}")

PACKAGE_NAME = f"{APP_NAME}-{VERSION}.tar.gz"

# --- Start Script ---
print(f"Creating package for {APP_NAME} version {VERSION}...")

# 1. Clean up previous build and create directories
print("--> Cleaning up previous build...")
if os.path.exists(BUILD_DIR):
    shutil.rmtree(BUILD_DIR)

# 2. Copy all necessary files, preserving directory structure
print("--> Copying application files...")

# Define patterns for files and directories to exclude from the package.
# This is more robust than an explicit include list.
ignore_patterns = shutil.ignore_patterns(
    'test',          # Exclude the test directory
    'Packaging',     # Exclude the packaging directory
    '.gitignore',    # Exclude git files
    'build',         # Exclude the build directory itself
    '__pycache__',   # Exclude python cache directories
    '*.pyc',         # Exclude python cache files
    'venv',          # Exclude virtual environment
    '.venv'          # Exclude virtual environment (common alternative name)
)

# Copy the entire source root to the package directory, excluding ignored files.
shutil.copytree(SOURCE_ROOT, PACKAGE_DIR, ignore=ignore_patterns)

# 3. Create the compressed archive
archive_path = os.path.join(BUILD_DIR, PACKAGE_NAME)
print(f"--> Creating archive: {archive_path}")
with tarfile.open(archive_path, "w:gz") as tar:
    # The arcname parameter removes the 'build/' part from the path inside the tarball
    tar.add(PACKAGE_DIR, arcname=APP_NAME)

print("\nPackage created successfully!")
print(f"File: {archive_path}")