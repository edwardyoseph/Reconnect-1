#!/bin/bash

LOG_FILE="/sdcard/log.txt"   # Lokasi file log
ACT="com.roblox.client.startup.ActivitySplash"

while true; do
    awk -v RS="--------------------------------------------------" '
    NF > 0 {
        username="";
        client="";
        status="";
        for(i=1;i<=NF;i++){
            if($i=="Username:"){ username=$(i+1) }
            if($i=="ClientName:"){ client=$(i+1) }
            if($i=="Status:"){ status=$(i+1) }
        }
        printf "%s|%s|%s\n", username, client, status
    }' "$LOG_FILE" | while IFS="|" read -r USER CLIENT STATUS
    do
        [ -z "$CLIENT" ] && continue

        if [ "$STATUS" = "Offline" ]; then
            echo "[OFFLINE] Restart Roblox + Join PS"
            
            adb shell am force-stop "$CLIENT"
            sleep 5

            am start -n "$CLIENT/$ACT"
            sleep 10

            am start -a android.intent.action.VIEW -d "$PS_LINK" -p "$CLIENT"
            sleep 35
        fi

        if [ "$STATUS" = "Home" ]; then
            echo "[HOME] Join Private Server"

            am start -a android.intent.action.VIEW -d "$PS_LINK" -p "$CLIENT"
            sleep 35
        fi

    done
    sleep 30
done
