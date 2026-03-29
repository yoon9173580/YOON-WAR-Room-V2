#!/usr/bin/env python3
"""
Realistic GME Pipeline Launcher
Opens the browser with realistic constraints applied
"""

import webbrowser
import os
import sys

def main():
    print("=" * 60)
    print("YOON MASTER COMMAND - Realistic Pipeline Launcher")
    print("=" * 60)
    
    # Check if realistic pipeline HTML exists
    html_file = 'realistic_pipeline.html'
    
    if not os.path.exists(html_file):
        print(f"Error: {html_file} not found!")
        print("Please run 'python realistic_pipeline.py' first.")
        return 1
    
    # Open in browser
    try:
        file_path = os.path.abspath(html_file)
        file_url = f"file://{file_path}"
        
        print(f"Opening realistic pipeline...")
        webbrowser.open(file_url)
        
        print("\n" + "=" * 60)
        print("Realistic GME Pipeline Loaded!")
        print("=" * 60)
        print("\nApplied Retail Constraints:")
        print("  - Fidelity option limit: $500,000")
        print("  - Moomoo option limit: $750,000")
        print("  - CS stock maximum: 50,000 shares")
        print("  - Strike contracts max: 1,000 per strike")
        print("  - 37:63 ratio maintained (Fid:Moo)")
        print("\nRealistic Allocation Strategy:")
        print("  - ST 2: Fixed immediate consumption")
        print("  - ST 3: Limited by platform constraints")
        print("  - Final cash: Remainder after allocations")
        print("\nDashboard opened in browser!")
        
    except Exception as e:
        print(f"Error opening browser: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
