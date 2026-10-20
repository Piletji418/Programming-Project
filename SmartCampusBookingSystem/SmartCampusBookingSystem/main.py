#!/usr/bin/env python3
"""
Smart Campus Resource Booking System
Programming 512 Assignment - Richfield Graduate Institution

Entry point for the application.
Run: python main.py
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from gui import main

if __name__ == "__main__":
    main()
