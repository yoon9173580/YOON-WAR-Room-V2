#!/usr/bin/env python3
"""
Adjusted GME Pipeline Launcher
ST 2 adjusted to $600K, 100K units, clickable amounts
"""

import webbrowser
import os
import sys

def main():
    print("=" * 70)
    print("YOON MASTER COMMAND - Adjusted Pipeline Launcher")
    print("=" * 70)
    
    # Check if adjusted pipeline HTML exists
    html_file = 'adjusted_pipeline.html'
    
    if not os.path.exists(html_file):
        print(f"Error: {html_file} not found!")
        print("Please run 'python adjusted_pipeline.py' first.")
        return 1
    
    # Open in browser
    try:
        file_path = os.path.abspath(html_file)
        file_url = f"file://{file_path}"
        
        print(f"Opening adjusted pipeline...")
        webbrowser.open(file_url)
        
        print("\n" + "=" * 70)
        print("ADJUSTED GME PIPELINE LOADED!")
        print("=" * 70)
        print("\nKEY ADJUSTMENTS:")
        print("  • ST 2 Immediate Rewards: $600,000 (increased)")
        print("  • All amounts displayed in million units")
        print("  • All numbers rounded down to 0000")
        print("  • Click any amount to see actual value")
        print("  • Proportional recalculations applied")
        
        print("\nDISPLAY FEATURES:")
        print("  • Million Unit Display: Easy to read large numbers")
        print("  • Clickable Amounts: Hover and click for actual values")
        print("  • Rounded Values: All numbers end with 0000")
        print("  • Tooltips: Show exact amounts on click")
        print("  • Color Coding: Negative (red), Positive (green)")
        
        print("\nCALCULATION BASE:")
        print("  • ST 2: $600,000 (adjusted from $578,788)")
        print("  • CS Shares: 100,000 shares at current price")
        print("  • Options: Precise contract calculations")
        print("  • Cash Reserves: Remainder after allocations")
        
        print("\nUSER INTERFACE:")
        print("  • Click any amount to see actual dollar value")
        print("  • All large numbers in 100K units for readability")
        print("  • Automatic rounding to 0000 for clean display")
        print("  • Responsive design for all screen sizes")
        
        print("\nDashboard opened in browser!")
        print("   Click any amount to see the actual value...")
        
    except Exception as e:
        print(f"Error opening browser: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
