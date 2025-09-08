#!/usr/bin/env python3
"""Simple runner script for collecting unreplied reviews."""

import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from collectors.review_collector import main

if __name__ == "__main__":
    main()