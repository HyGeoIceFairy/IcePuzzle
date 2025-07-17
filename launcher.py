import tkinter as tk
from tkinter import ttk, messagebox
import requests
import zipfile
import io
import json
from pathlib import Path
import sys
import platform

SERVER_VERSION_URL = "https://raw.githubusercontent.com/HyGeoIceFairy/Program/refs/heads/main/IcePuzzle/version.json?token=GHSAT0AAAAAAC7WX3CAECDLA5VTXR4QEA3C2DYYXXQ"
UPDATE_ZIP_URL = "https://example.com/update.zip"

PROJECT_ROOT = Path(__file__).parent
LOCAL_VERSION_FILE = PROJECT_ROOT / "version.json"

def get_local_version():
    if not LOCAL_VERSION_FILE.exists():
        return None
    with open(LOCAL_VERSION_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("version")


def get_server_version():
    try:
        r = requests.get(SERVER_VERSION_URL, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data.get("version"), data.get("changelog", [])
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


class UpdateGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Updater")
        self.geometry("400x150")
        self.resizable(False, False)

        self.label = ttk.Label(self, text="Check Update")
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
            messagebox.showerror("Error", "无法连接服务器获取版本信息！")
            self.update_button.config(state="normal")
            return

        if local_version is None or compare_versions(local_version, server_version):
            # 有更新
            if messagebox.askyesno("更新提示",
                                   f"检测到新版本：{server_version}\n更新日志：\n" + "\n".join(changelog) + "\n是否下载更新？"):
                try:
                    buf = download_update(self.progress_update)
                except Exception as e:
                    messagebox.showerror("错误", f"下载失败：{e}")
                    self.update_button.config(state="normal")
                    return

                if verify_zip(buf):
                    extract_update(buf)
                    messagebox.showinfo("成功", "更新完成，请重启程序！")
                else:
                    messagebox.showerror("错误", "下载的更新包校验失败！")
            else:
                self.label.config(text="用户取消更新。")
        else:
            messagebox.showinfo("提示", "当前已经是最新版本！")

        self.update_button.config(state="normal")
        self.progress["value"] = 0
        self.label.config(text="检查更新完成。")


if __name__ == "__main__":
    app = UpdateGUI()
    app.mainloop()
