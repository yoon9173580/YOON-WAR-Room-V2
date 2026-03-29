#!/usr/bin/env python3
"""
Dynamic GME Pipeline Launcher
Starts both the price server and opens the enhanced dashboard
"""

import subprocess
import sys
import time
import webbrowser
from threading import Thread

def start_price_server():
    """Start the Flask price server"""
    try:
        print("Starting GME Price Server...")
        server_process = subprocess.Popen([
            sys.executable, 'price_server.py'
        ], cwd='.')
        
        # Wait a moment for server to start
        time.sleep(3)
        
        # Check if server started successfully
        if server_process.poll() is None:
            print("✅ Price Server started successfully on http://localhost:5000")
            return server_process
        else:
            print("❌ Price Server failed to start")
            return None
            
    except Exception as e:
        print(f"❌ Error starting price server: {e}")
        return None

def open_dashboard():
    """Open the enhanced dashboard in browser"""
    try:
        dashboard_url = f"file://{webbrowser.os.path.abspath('enhanced_index.html')}"
        print(f"Opening dashboard: {dashboard_url}")
        webbrowser.open(dashboard_url)
        print("✅ Dashboard opened in browser")
    except Exception as e:
        print(f"❌ Error opening dashboard: {e}")

def main():
    print("=" * 60)
    print("🚀 YOON MASTER COMMAND - Dynamic Pipeline Launcher")
    print("=" * 60)
    
    # Check if required files exist
    required_files = ['price_server.py', 'enhanced_index.html']
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        print("Please ensure all pipeline files are present.")
        return
    
    # Start price server
    server_process = start_price_server()
    
    if server_process:
        # Open dashboard after server starts
        time.sleep(2)
        open_dashboard()
        
        print("\n" + "=" * 60)
        print("📊 Dynamic Pipeline is now running!")
        print("=" * 60)
        print("🔗 Price Server API: http://localhost:5000")
        print("🔗 Dashboard: Opened in browser")
        print("🔗 API Endpoints:")
        print("   - GET /api/gme-price - Current GME price")
        print("   - GET /api/health - Server health check")
        print("\n💡 Features:")
        print("   ✨ Real-time GME price updates every 30 seconds")
        print("   ✨ Dynamic pipeline value calculations")
        print("   ✨ Market hours detection")
        print("   ✨ Enhanced visual interface")
        print("   ✨ Price change animations")
        print("\n⚠️  Press Ctrl+C to stop the server")
        print("=" * 60)
        
        try:
            # Keep server running
            server_process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Stopping price server...")
            server_process.terminate()
            server_process.wait()
            print("✅ Server stopped")
    else:
        print("❌ Failed to start dynamic pipeline")
        return 1
    
    return 0

if __name__ == "__main__":
    import os
    sys.exit(main())
