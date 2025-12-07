while true; do
echo "flush RAM in 15 minutes..."
sleep 900  # Jeda selama 8 jam (28800 detik)
  echo "FLUSHING RAM..."
  sleep 2
    for app in $(cmd package list packages -3 | cut -f 2 -d ":"); do
    # Cek jika aplikasi bukan "me.piebridge.brevent", "eu.sisik.hackendebug", atau "com.termux"
    if [[ ! "$app" == "me.piebridge.brevent" ]] && [[ ! "$app" == "eu.sisik.hackendebug" ]] && [[ ! "$app" == "com.termux" ]]; then
        # Menampilkan aplikasi yang dihentikan
        echo "Force Stop Apps For Flush RAM $app"
        
        # Menhentikan aplikasi dengan perintah force-stop
        cmd activity force-stop "$app"
        
        # Memberi jeda 1 detik
        sleep 1
        echo ""
    fi
    done
    echo "RAM FLUSHED SUCCESSFULLY"
done
