import subprocess
import requests
import time
import psutil
import os
import aiofiles
import asyncio

# Webhook URL for Discord
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Array to store collected data temporarily
data_buffer = {}

# Log file path
log_file_path = "/sdcard/log.txt"

# Function to run adb commands directly
def run_adb_command(command):
    # Runs adb command and returns the result
    result = subprocess.run(f"adb shell {command}", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    return result.stdout.decode("utf-8")

# Function to get Roblox user status (Home/In-Game) using the Presence API
def get_user_status(user_id):
    try:
        url = "https://presence.roblox.com/v1/presence/users"
        body = {"userIds": [user_id]}  
        headers = {'Content-Type': 'application/json'}

        response = requests.post(url, json=body, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            presences = data.get("userPresences", [])
            if not presences:
                return "Offline"  # Default if no data found

            presence = presences[0]
            status_code = presence.get("userPresenceType", -1)
            
            # Update this line to map "Online" to "Home"
            status_map = {0: "Offline", 1: "Home", 2: "In-Game", 3: "In Studio"}
            status = status_map.get(status_code, "Unknown")
            
            # Keep "In Studio" as "Home" to avoid confusion, as it represents the home page in Roblox
            if status == "In Studio":
                return "Home"
                
            return status
        else:
            return "Offline"
    except Exception as e:
        return "Offline"

def open_roblox(pkg):
    print(f"⏳ Opening Roblox with package: {pkg}...")

    # Open Roblox application with adb command
    run_adb_command(f"am start -n {pkg}/com.roblox.client.startup.ActivitySplash")
    time.sleep(30)  # Wait for Roblox to launch

# Function to update the log file using aiofiles (asynchronous I/O)
async def update_log_file(data):
    async with aiofiles.open(log_file_path, 'w') as log_file:
        for user, user_data in data.items():
            await log_file.write(f"Username: {user_data['username']}\n")
            await log_file.write(f"UserId: {user_data['user_id']}\n")
            await log_file.write(f"PID: {user_data['pid']}\n")
            await log_file.write(f"ClientName: {user_data['client_name']}\n")
            await log_file.write(f"Status: {user_data['status']}\n")
            await log_file.write("-" * 50 + "\n")

# Find all packages related to Roblox (client)
pkg_command = "pm list packages | grep -i 'com.roblox'"
pkg_output = run_adb_command(pkg_command).strip()
packages = [pkg.split(":")[1].strip() for pkg in pkg_output.splitlines()]
packages_sorted = sorted(packages)

# Loop through each package and gather data
for client_pkg in packages_sorted:
    # Buka Roblox
    open_roblox(client_pkg)

    # Cari PID dari client yang sudah dibuka
    pid_command = f"pgrep -f {client_pkg}"
    pid_output = run_adb_command(pid_command).strip()

    if pid_output:
        pid = pid_output
        print(f"✅ Client: {client_pkg} (PID: {pid})")

        # Gunakan logcat untuk mencari data login berdasarkan PID
        logcat_command = f"logcat -d | grep -F {pid} | grep -i 'DID_LOG_IN'"
        logcat_output = run_adb_command(logcat_command)

        if logcat_output:
            username = None
            user_id = None

            for line in logcat_output.splitlines():
                if "username" in line:
                    username = line.split('"username":"')[1].split('"')[0]
                if "userId" in line:
                    user_id = line.split('"userId":')[1].split(",")[0]

            if username and user_id:
                # Ambil status dari API
                status = get_user_status(user_id)
                print(f"⭐ Found - Username: {username}, UserId: {user_id}, Status: {status}")

                # Simpan data ke buffer
                data_buffer[username] = {
                    "username": username,
                    "user_id": user_id,
                    "pid": pid,
                    "client_name": client_pkg,
                    "status": status
                }
        else:
            print(f"⚠️ No login data found for client with PID {pid}")
    else:
        print(f"❌ Client {client_pkg} is not running.")
            
asyncio.run(update_log_file(data_buffer))
