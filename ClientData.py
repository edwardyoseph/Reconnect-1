import subprocess
import requests
import time
import aiofiles
import asyncio

data_buffer = {}
log_file_path = "/sdcard/Reconnect/log.txt"

def run_adb_command(command):
    result = subprocess.run(f"adb shell {command}", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    return result.stdout.decode("utf-8")

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
                return "Offline"
            
            presence = presences[0]
            status_code = presence.get("userPresenceType", -1)
            status_map = {0: "Offline", 1: "Home", 2: "In-Game", 3: "In Studio"}
            status = status_map.get(status_code, "Unknown")
            if status == "In Studio":
                return "Home"
                
            return status
        else:
            return "Offline"
    except Exception as e:
        return "Offline"

def open_roblox(pkg):
    print(f"⏳ Opening Roblox with package: {pkg}...")
    run_adb_command(f"am start -n {pkg}/com.roblox.client.startup.ActivitySplash")
    time.sleep(30)
    
async def update_log_file(data):
    async with aiofiles.open(log_file_path, 'w') as log_file:
        for user, user_data in data.items():
            await log_file.write(f"Username: {user_data['username']}\n")
            await log_file.write(f"UserId: {user_data['user_id']}\n")
            await log_file.write(f"PID: {user_data['pid']}\n")
            await log_file.write(f"ClientName: {user_data['client_name']}\n")
            await log_file.write(f"Status: {user_data['status']}\n")
            await log_file.write("-" * 50 + "\n")

pkg_command = "pm list packages | grep -i 'com.roblox'"
pkg_output = run_adb_command(pkg_command).strip()
packages = [pkg.split(":")[1].strip() for pkg in pkg_output.splitlines()]
packages_sorted = sorted(packages)

for client_pkg in packages_sorted:
    time.sleep(1)
    open_roblox(client_pkg)

    pid_command = f"pgrep -f {client_pkg}"
    pid_output = run_adb_command(pid_command).strip()

    if pid_output:
        pid = pid_output
        print(f"✅ Client: {client_pkg} (PID: {pid})")
        
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
                status = get_user_status(user_id)
                print(f"⭐ Found - Username: {username}, UserId: {user_id}, Status: {status}")
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
print(f"Log file Finished")
