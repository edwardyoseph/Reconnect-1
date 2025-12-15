import subprocess
import requests
import time
import psutil
import os
import aiofiles
import asyncio

# Path to the file that contains the webhook URL
WEBHOOK_FILE_PATH = "/sdcard/Reconnect/webhookurl.txt"

# Read the webhook URL from the file
def read_webhook_url(file_path):
    try:
        with open(file_path, 'r') as file:
            webhook_url = file.read().strip()  # Remove any surrounding whitespace
            if webhook_url:
                return webhook_url
            else:
                print("❌ Webhook URL is empty in the file.")
                return None
    except FileNotFoundError:
        print(f"❌ Webhook URL file not found at {file_path}.")
        return None

# Webhook URL for Discord (read from the file)
WEBHOOK_URL = read_webhook_url(WEBHOOK_FILE_PATH)

# Array to store collected data temporarily
data_buffer = {}

# Log file path
log_file_path = "/storage/emulated/0/Reconnect/log.txt"

# Function to read the log file and populate data_buffer
def parse_log_file():
    global data_buffer
    try:
        with open(log_file_path, 'r') as file:
            lines = file.readlines()
            user_data = {}
            for line in lines:
                if "Username:" in line:
                    username = line.split(":")[1].strip()
                elif "UserId:" in line:
                    user_id = line.split(":")[1].strip()
                elif "PID:" in line:
                    pid = line.split(":")[1].strip()
                elif "ClientName:" in line:
                    client_name = line.split(":")[1].strip()
                elif "Status:" in line:
                    status = line.split(":")[1].strip()
                    # Add the data to buffer
                    user_data = {
                        "username": username,
                        "user_id": user_id,
                        "pid": pid,
                        "client_name": client_name,
                        "status": status
                    }
                    data_buffer[username] = user_data
    except FileNotFoundError:
        print("❌ Log file not found.")
    except Exception as e:
        print(f"Error parsing log file: {e}")

# Function to get the status of a user from Roblox API
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
        print(f"Error fetching user status: {e}")
        return "Offline"

# Function to update only the status in the data buffer
def update_status_in_buffer():
    global data_buffer
    for username, user_data in data_buffer.items():
        updated_status = get_user_status(user_data["user_id"])
        if updated_status != user_data["status"]:
            print(f"Status updated for {user_data['username']} from {user_data['status']} to {updated_status}")
            user_data["status"] = updated_status  # Update the status in the buffer

# Function to get device usage (CPU, RAM)
def get_device_usage():
    cpu_usage = psutil.cpu_percent(interval=1)

    mem = psutil.virtual_memory()
    total_gb = mem.total / (1024 ** 3)
    used_gb = (mem.total - mem.available) / (1024 ** 3)

    total_gb = f"{total_gb:.2f}GB"
    used_gb = f"{used_gb:.2f}GB"

    return cpu_usage, used_gb, total_gb

def generate_bar(percent, length=18):
    filled = int(length * (percent / 100))
    empty = length - filled
    return "█" * filled + "░" * empty

def choose_color(cpu):
    if cpu < 40:
        return 5793266   # green-blue
    elif cpu < 70:
        return 16753920  # yellow
    else:
        return 15158332  # red

def send_to_webhook(data):
    if not WEBHOOK_URL:
        print("❌ Webhook URL is not available.")
        return

    cpu, ram_used, ram_total = get_device_usage()

    ram_used_float = float(ram_used.replace("GB", ""))
    ram_total_float = float(ram_total.replace("GB", ""))
    ram_percent = (ram_used_float / ram_total_float) * 100

    cpu_bar = generate_bar(cpu)
    ram_bar = generate_bar(ram_percent)

    embed_color = choose_color(cpu)

    embeds = []

    # ===== EMBED 1: Device Status =====
    device_embed = {
        "title": "📘 Cloud Phone Device Status",
        "color": embed_color,
        "fields": [
            {
                "name": "📟 CPU Usage",
                "value": f"**{cpu}%**\n`{cpu_bar}`",
                "inline": False
            },
            {
                "name": "🧠 RAM Usage",
                "value": f"**{ram_used} / {ram_total}**\n`{ram_bar}`",
                "inline": False
            }
        ],
        "footer": {"text": "Auto Update • Every 5 Minute"}
    }

    embeds.append(device_embed)

    # ===== EMBED 2: Roblox Bot Status =====
    bot_embed = {
        "title": "🤖 Roblox Bot Status",
        "color": 5793266,
        "fields": []
    }

    for user, user_data in data.items():
        bot_embed["fields"].append({
            "name": f"✨ {user_data['username']}",
            "value": (
                f"**UserId:** {user_data['user_id']}\n"
                f"**PID:** {user_data['pid']}\n"
                f"**Client:** `{user_data['client_name']}`\n"
                f"**Status:** **{user_data['status']}**"
            ),
            "inline": False
        })

    embeds.append(bot_embed)

    # ===== SEND TO DISCORD =====
    payload = {"embeds": embeds}
    try:
        r = requests.post(WEBHOOK_URL, json=payload)
        if r.status_code == 204:
            print("✅ Embed sent successfully.")
        else:
            print("❌ Failed to send embed:", r.status_code, r.text)
    except Exception as e:
        print(f"Error sending webhook: {e}")

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

# Function to run the status update loop
async def status_update_loop():
    global data_buffer
    parse_log_file()  # Read the log file at the start
    last_sent_time = time.time()

    while True:
        await asyncio.sleep(30)  # Wait for 30 seconds before updating status

        update_status_in_buffer()  # Update user status in the buffer

        # Update the log file
        await update_log_file(data_buffer)

        # Send data to webhook every 5 minutes
        if time.time() - last_sent_time >= 300:
            send_to_webhook(data_buffer)  # Send the updated data to Discord webhook
            last_sent_time = time.time()  # Update the last sent time

# Start
