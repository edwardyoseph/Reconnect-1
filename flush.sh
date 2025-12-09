while true; do
sleep 300
echo "flush RAM in 15 minutes..."
sleep 18000  # Jeda selama 8 jam (28800 detik)
  echo "FLUSHING RAM..."
  sleep 2
    for pkg in $(adb shell pm list packages -3 | cut -f 2 -d ":"); do
        # Mengecualikan Termux dari proses penghapusan cache
        if [[ "$pkg" != "com.termux" ]]; then
            adb shell pm clear $pkg
            sleep 1  # Memberi jeda 1 detik antara setiap aplikasi
        fi
    done
    echo "RAM FLUSHED SUCCESSFULLY"
done
