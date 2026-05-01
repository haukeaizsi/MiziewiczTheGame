#!/usr/bin/env python
"""
Setup script for Miziewicz The Game
"""
import subprocess
import sys

def install_requirements():
    """Install required packages from requirements.txt"""
    print("Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    print("\n✓ Dependencies installed successfully!")
    print("\nTo play local game (Pygame):")
    print("  python miz.py")

if __name__ == "__main__":
    try:
        install_requirements()
    except Exception as e:
        print(f"\n✗ Installation failed: {e}")
        sys.exit(1)
