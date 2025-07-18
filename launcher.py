import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
import zipfile
import io
import json
import subprocess
import os
import sys
import platform

SERVER_VERSION_URL = "https://raw.githubusercontent.com/HyGeoIceFairy/IcePuzzle/refs/heads/main/version.json"
UPDATE_ZIP_URL = "https://github.com/HyGeoIceFairy/IcePuzzle/releases/download/v0.1.1/IcePuzzle.zip"

if getattr(sys, 'frozen', False):
    PROJECT_ROOT = os.path.dirname(sys.executable)
    os.chdir(PROJECT_ROOT)
else:
    PROJECT_ROOT = os.path.dirname(__file__)
    os.chdir(PROJECT_ROOT)
LOCAL_VERSION_FILE = os.path.join(PROJECT_ROOT, "version.json")


def get_local_version():
    if not os.path.exists(LOCAL_VERSION_FILE):
        return None
    with open(LOCAL_VERSION_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("version")


def get_server_version():
    try:
        r = requests.get(SERVER_VERSION_URL, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data.get("version"), data.get("changeLog", [])
    except Exception as e:
        return None, []


def compare_versions(local, server):
    return local != server


def download_update(progress_callback):
    r = requests.get(UPDATE_ZIP_URL, stream=True)
    r.raise_for_status()
    total_length = int(r.headers.get('content-length', 0))
    downloaded = 0
    buf = io.BytesIO()

    for chunk in r.iter_content(chunk_size=8192):
        if chunk:
            buf.write(chunk)
            downloaded += len(chunk)
            progress_callback(downloaded, total_length)
    buf.seek(0)
    return buf


def verify_zip(file_like):
    try:
        with zipfile.ZipFile(file_like) as zf:
            bad_file = zf.testzip()
            return bad_file is None
    except:
        return False


def extract_update(file_like):
    with zipfile.ZipFile(file_like) as zf:
        zf.extractall(PROJECT_ROOT)


def start_main():
    main_exe = os.path.join(PROJECT_ROOT, "main.exe")
    if os.path.exists(main_exe):
        subprocess.Popen(["cmd", "/c", "start", "", str(main_exe)], shell=True)
    else:
        messagebox.showwarning(
            "Warning", "Cannot find \"main.exe\". Please start manually.")


class UpdateGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Updater")
        self.geometry("400x150")
        self.resizable(False, False)

        bg_color = self.cget("bg")

        self.label = tk.Label(
            self, text="Automatically start updater.", bg=bg_color, width=50, anchor="center")
        self.label.pack(pady=10)

        self.progress = ttk.Progressbar(self, length=350, mode="determinate")
        self.progress.pack(pady=10)

        self.update_button = ttk.Button(
            self, text="Check Update", command=self.check_update)
        self.update_button.pack()

    def progress_update(self, downloaded, total):
        if total > 0:
            percent = int(downloaded / total * 100)
            self.progress["value"] = percent
            self.label.config(text=f"Downloading... {percent}%")
            self.update_idletasks()

    def check_update(self):
        self.update_button.config(state="disabled")
        local_version = get_local_version()
        server_version, changelog = get_server_version()

        if server_version is None:
            messagebox.showerror(
                "Error", "Cannot connect to the server. Maybe you can try VPN.")
            self.update_button.config(state="normal")
            return

        if local_version is None or compare_versions(local_version, server_version):
            if messagebox.askyesno("Update tips:",
                                   f"New version detected: {server_version}\nChangelog:\n" + "\n".join(changelog) + "\nDownload?"):
                try:
                    buf = download_update(self.progress_update)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to download.\n{e}")
                    self.update_button.config(state="normal")
                    return

                if verify_zip(buf):
                    extract_update(buf)
                    messagebox.showinfo(
                        "Success", "Succeeded. Restart the program.")
                    start_main()
                else:
                    messagebox.showerror("Error", "Failed to verify the zip.")
            else:
                self.label.config(text="Update cancelled.")
        else:
            messagebox.showinfo("Tip", "You have the latest version!")
            start_main()

        self.update_button.config(state="normal")
        self.progress["value"] = 0
        self.label.config(text="Succeeded to check update.")


if __name__ == "__main__":
    app = UpdateGUI()
    app.mainloop()
