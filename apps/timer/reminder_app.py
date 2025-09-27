import tkinter as tk
from tkinter import messagebox, filedialog
import os
from pathlib import Path
from playsound import playsound # Assuming playsound is installed

class ReminderApp:
    def __init__(self, master):
        self.master = master
        master.title("Desktop Reminder")

        self.interval_minutes = tk.StringVar(value="1") # Default to 1 minute
        self.message_text = tk.StringVar(value="Time to Save Project!")
        default_audio = Path(__file__).with_name("Do Something.wav")
        self.audio_file_path = tk.StringVar(value=str(default_audio))

        self.timer_id = None # To store the ID of the scheduled event

        # --- Widgets ---
        tk.Label(master, text="Interval (minutes):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.interval_entry = tk.Entry(master, textvariable=self.interval_minutes, width=10)
        self.interval_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(master, text="Message:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.message_entry = tk.Entry(master, textvariable=self.message_text, width=40)
        self.message_entry.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky="ew")

        tk.Label(master, text="Audio File (.wav, .mp3):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.audio_path_entry = tk.Entry(master, textvariable=self.audio_file_path, width=40)
        self.audio_path_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        self.browse_button = tk.Button(master, text="Browse", command=self.browse_audio_file)
        self.browse_button.grid(row=2, column=2, padx=5, pady=5)

        self.start_button = tk.Button(master, text="Start Reminder", command=self.start_reminder)
        self.start_button.grid(row=3, column=0, columnspan=2, pady=10)

        self.stop_button = tk.Button(master, text="Stop Reminder", command=self.stop_reminder, state=tk.DISABLED)
        self.stop_button.grid(row=3, column=1, columnspan=2, pady=10)

        # Configure column weights for resizing
        master.grid_columnconfigure(1, weight=1)

    def browse_audio_file(self):
        default_dir = Path(__file__).parent
        file_path = filedialog.askopenfilename(
            initialdir=str(default_dir),
            initialfile="Do Something.wav",
            filetypes=[("Audio Files", "*.wav *.mp3"), ("All Files", "*.*")]
        )
        if file_path:
            self.audio_file_path.set(file_path)

    def start_reminder(self):
        try:
            interval = float(self.interval_minutes.get())
            if interval <= 0:
                messagebox.showerror("Invalid Input", "Interval must be a positive number.")
                return
        except ValueError:
            messagebox.showerror("Invalid Input", "Interval must be a number.")
            return

        audio_path = self.audio_file_path.get()
        if audio_path and not os.path.exists(audio_path):
            messagebox.showwarning("Audio File Warning", "Audio file not found. Reminder will proceed without sound.")
            # Don't return, allow reminder to start without sound

        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.interval_entry.config(state=tk.DISABLED)
        self.message_entry.config(state=tk.DISABLED)
        self.audio_path_entry.config(state=tk.DISABLED)
        self.browse_button.config(state=tk.DISABLED)

        messagebox.showinfo("Reminder Started", f"Reminder set to trigger every {interval} minutes.")
        self.schedule_reminder(interval)

    def schedule_reminder(self, interval):
        # Convert minutes to milliseconds
        delay_ms = int(interval * 60 * 1000)
        self.timer_id = self.master.after(delay_ms, self.trigger_reminder, interval)

    def trigger_reminder(self, interval):
        message = self.message_text.get()
        audio_path = self.audio_file_path.get()

        # Play sound if path is valid
        if audio_path and os.path.exists(audio_path):
            try:
                playsound(audio_path, block=False) # block=False to not block the GUI
            except Exception as e:
                print(f"Error playing sound: {e}")
                messagebox.showerror("Audio Playback Error", f"Could not play audio file: {e}")

        # Display message
        messagebox.showinfo("Reminder!", message)

    def stop_reminder(self):
        if self.timer_id:
            self.master.after_cancel(self.timer_id)
            self.timer_id = None
        messagebox.showinfo("Reminder Stopped", "The reminder has been stopped.")

        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.interval_entry.config(state=tk.NORMAL)
        self.message_entry.config(state=tk.NORMAL)
        self.audio_path_entry.config(state=tk.NORMAL)
        self.browse_button.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = ReminderApp(root)
    root.mainloop()
