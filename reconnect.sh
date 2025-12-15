#!/bin/bash

LOG_FILE="/sdcard/Reconnect/log.txt"
ACT="com.roblox.client.startup.ActivitySplash"
PS_LINK_FILE="/sdcard/Reconnect/linkps.txt"

if [[ -f "$PS_LINK_FILE" ]]; then
    PS_LINK=$(cat "$PS_LINK_FILE" | tr -d '\r')
    if [[ -z "$PS_LINK" ]]; then
        echo "❌ Link PS di file $PS_LINK_FILE kosong!"
        exit 1
    fi
else
    echo "❌ File $PS_LINK_FILE tidak ditemukan!"
    exit 1
fi

echo "✅ Link PS berhasil dibaca: $PS_LINK"

while true; do
    awk -v RS="--------------------------------------------------" '
    NF > 0 {
        username="";
        client="";
        status="";
        for(i=1; i<=NF; i++){
            if($i == "Username:"){ username=$(i+1) }
            if($i == "ClientName:"){ client=$(i+1) }
            if($i == "Status:"){ status=$(i+1) }
        }
        printf "%s|%s|%s\n", username, client, status
    }' "$LOG_FILE" | while IFS="|" read -r USER CLIENT STATUS
    do
        [ -z "$CLIENT" ] && continue
        if [ "$STATUS" = "Offline" ]; then
            echo "[OFFLINE] Restart Roblox + Join PS"
            adb shell am force-stop "$CLIENT"
            sleep 5
            adb shell am start -n "$CLIENT/$ACT"
            sleep 10
            adb shell am start -a android.intent.action.VIEW -d "$PS_LINK" -p "$CLIENT"
            sleep 35
        fi

        if [ "$STATUS" = "Home" ]; then
            echo "[HOME] Join Private Server"
            adb shell am start -a android.intent.action.VIEW -d "$PS_LINK" -p "$CLIENT"
            sleep 35
        fi

    done
    sleep 30
done
