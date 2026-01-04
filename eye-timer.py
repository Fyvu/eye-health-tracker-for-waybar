import sys
import json
import time
import signal
import os
import subprocess

# Konfigurasi
WORK_TIME = 10  # 1200 detik
BREAK_TIME = 20      # 20 detik
STATE_FILE = "/tmp/eye_timer_state.json"
NOTIF_SOUND = os.path.expanduser("~/Personal-Lib/soundEffect/new-notification-022-370046_1.mp3")


class EyeTimer:
    def __init__(self):
        self.running = False
        self.state = "IDLE"  # IDLE, WORK, BREAK, PAUSED
        self.time_left = WORK_TIME
        self.total_work_seconds = 0
        self.start_uptime = time.time()
        
        # Load state jika ada
        self.load_state()

    def send_notification(self,  msg, sound=True):
        subprocess.run(["hyprctl", "notify", "1", "300", "rgb(ff0000)", msg])
        
        if sound:
            # Menggunakan pw-play (Pipewire)
            # Pastikan NOTIF_SOUND sudah di-expand atau gunakan absolute path
            subprocess.Popen(["pw-play", NOTIF_SOUND])

    def toggle(self):
        if self.state == "IDLE" or self.state == "PAUSED":
            self.state = "WORK"
            self.running = True
        elif self.state == "WORK":
            self.state = "PAUSED"
            self.running = False
        self.save_state()

    def reset(self):
        self.state = "WORK"
        self.time_left = WORK_TIME
        self.running = True
        self.save_state()

    def stop(self):
        self.state = "IDLE"
        self.time_left = WORK_TIME
        self.running = False
        self.save_state()

    def update(self):
        if self.running:
            self.time_left -= 1
            if self.state == "WORK":
                self.total_work_seconds += 1
                if self.time_left <= 0:
                    self.state = "BREAK"
                    self.time_left = BREAK_TIME
                    self.send_notification("Break Time! | Look 20 feet away for 20 seconds.")
            
            elif self.state == "BREAK":
                if self.time_left <= 0:
                    self.state = "WORK"
                    self.time_left = WORK_TIME
                    self.send_notification("Back to Work | Session started.")
        self.save_state()

    def get_output(self):
        mins, secs = divmod(self.time_left, 60)
        display_time = f"{mins:02d}:{secs:02d}"
        
        uptime_sec = int(time.time() - self.start_uptime)
        up_h, up_m = divmod(uptime_sec // 60, 60)
        
        work_m = self.total_work_seconds // 60
        
        status_icons = {"IDLE": "󰔟", "WORK": "󰈈 ", "BREAK": "󰓠 ", "PAUSED": "󰏤 "}
        icon = status_icons.get(self.state, "󰔟")

        data = {
            "text": f"{icon} {display_time}",
            "tooltip": (
                f"Status: {self.state}\n"
                f"Screen Time: {work_m}m\n"
                f"Uptime: {up_h}h {up_m}m\n"
                "Left Click: Start/Pause\n"
                "Right Click: Stop\n"
                "Middle Click: Reset"
            ),
            "class": self.state.lower()
        }
        return json.dumps(data)

    def save_state(self):
        # Implementasi penyimpanan state ke file (opsional untuk persistensi)
        pass

    def load_state(self):
        pass

timer = EyeTimer()

def signal_handler(sig, frame):
    if sig == signal.SIGUSR1: timer.toggle()
    elif sig == signal.SIGUSR2: timer.reset()
    elif sig == signal.SIGRTMIN+1: timer.stop()

signal.signal(signal.SIGUSR1, signal_handler)
signal.signal(signal.SIGUSR2, signal_handler)
signal.signal(signal.SIGRTMIN+1, signal_handler)

while True:
    print(timer.get_output())
    sys.stdout.flush()
    timer.update()
    time.sleep(1)
