import requests
import time

def check_backend_health():
    """Simple health check to see if backend is still running"""
    
    try:
        print("🏥 Checking backend health...")
        response = requests.get("http://127.0.0.1:8000/health", timeout=5)
        
        if response.status_code == 200:
            print("✅ Backend is healthy and responding!")
            return True
        else:
            print(f"⚠️ Backend responded with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Backend is not responding")
        return False
    except Exception as e:
        print(f"❌ Error checking health: {str(e)}")
        return False

def wait_for_completion():
    """Wait for the previous request to complete"""
    print("⏳ Waiting for previous request to complete...")
    
    for i in range(12):  # Wait up to 2 minutes
        print(f"⏰ Check {i+1}/12...")
        
        if check_backend_health():
            print("✅ Backend is still running and healthy!")
        else:
            print("❌ Backend may have stopped")
            break
            
        time.sleep(10)  # Wait 10 seconds between checks
    
    print("🔄 Health check complete")

if __name__ == "__main__":
    wait_for_completion() 