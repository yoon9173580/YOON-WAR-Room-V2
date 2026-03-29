#!/usr/bin/env python3
"""
Current Price GME Pipeline Launcher
Real-time calculations with exact contract numbers
"""

import webbrowser
import os
import sys

def main():
    print("=" * 70)
    print("YOON MASTER COMMAND - Current Price Pipeline Launcher")
    print("=" * 70)
    
    # Check if current price pipeline HTML exists
    html_file = 'current_price_pipeline.html'
    
    if not os.path.exists(html_file):
        print(f"Error: {html_file} not found!")
        print("Please run 'python current_price_pipeline.py' first.")
        return 1
    
    # Open in browser
    try:
        file_path = os.path.abspath(html_file)
        file_url = f"file://{file_path}"
        
        print(f"Opening current price pipeline...")
        webbrowser.open(file_url)
        
        print("\n" + "=" * 70)
        print("CURRENT PRICE GME PIPELINE LOADED!")
        print("=" * 70)
        print("\nREAL-TIME CALCULATIONS:")
        print("  • All calculations based on current GME price")
        print("  • 100,000 shares cost calculated at current price")
        print("  • Option contracts with precise premium pricing")
        print("  • Exact contract numbers specified")
        print("  • Feasibility check for 100K share purchase")
        
        print("\nPRECISE CALCULATIONS:")
        print("  • CS Shares: Exactly 100,000 shares at current price")
        print("  • Option Premiums: Calculated with intrinsic + time value")
        print("  • Contract Numbers: Exact count per strike")
        print("  • Share Exposure: Contracts x 100 shares each")
        print("  • Cash Reserves: Remainder after all allocations")
        
        print("\nFEATURES:")
        print("  • Real-time price updates")
        print("  • Strike-by-strike breakdown")
        print("  • ITM/OTM classification")
        print("  • Utilization rate visualization")
        print("  • Feasibility indicators")
        
        print("\nDashboard opened in browser!")
        print("   Shows exact calculations based on current GME price...")
        
    except Exception as e:
        print(f"Error opening browser: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
