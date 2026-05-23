#!/usr/bin/env python3
"""
Video/Audio Downloader — powered by yt-dlp + ffmpeg
Requires: pip install yt-dlp   +   ffmpeg on PATH
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import re
import shutil
import sys

try:
    import yt_dlp
except ImportError:
    print("yt-dlp not found. Install it with:  pip install yt-dlp")
    sys.exit(1)

import subprocess

def _find_ffmpeg():
    found = shutil.which("ffmpeg")
    if found:
        return os.path.dirname(found)
    try:
        subprocess.run(["ffmpeg", "-version"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return "" 
    except Exception:
        pass
    for candidate in [
        r"C:\ffmpeg\bin",
        r"C:\Program Files\ffmpeg\bin",
        r"C:\Program Files (x86)\ffmpeg\bin",
    ]:
        if os.path.isfile(os.path.join(candidate, "ffmpeg.exe")):
            return candidate
    return None

FFMPEG_LOCATION = _find_ffmpeg() 

# ── Palette ───────────────────────────────────────────────────────────────────
BG      = "#0f0f0f"
SURFACE = "#1c1c1c"
BORDER  = "#2e2e2e"
ACCENT  = "#e8ff00"
CYAN    = "#00e5ff"
FG      = "#f0f0f0"
FG_DIM  = "#555555"
RED     = "#ff4444"
GREEN   = "#00ff88"

F_TITLE  = ("Courier New", 20, "bold")
F_LABEL  = ("Courier New", 9,  "bold")
F_MONO   = ("Courier New", 9)
F_BTN    = ("Courier New", 11, "bold")
F_FMT    = ("Courier New", 11, "bold")

ANSI = re.compile(r"\x1b\[[0-9;]*m")
def strip(t): return ANSI.sub("", t)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DOWNLOADER")
        self.configure(bg=BG)
        self.resizable(False, False)

        try:
            from ctypes import windll, byref, sizeof, c_int
            HWND = windll.user32.GetParent(self.winfo_id())
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            val = c_int(1)
            windll.dwmapi.DwmSetWindowAttribute(
                HWND, DWMWA_USE_IMMERSIVE_DARK_MODE, byref(val), sizeof(val)
            )
        except Exception:
            pass

        self._url    = tk.StringVar()
        self._dest   = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Downloads"))
        self._fmt    = tk.StringVar(value="mp4")
        self._status = tk.StringVar(value="ready.")
        self._pct    = tk.DoubleVar(value=0.0)
        self._busy   = False

        self._build()
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{(self.winfo_screenwidth()-w)//2}+{(self.winfo_screenheight()-h)//2}")

        if FFMPEG_LOCATION is None:
            self._log("⚠  ffmpeg not found on PATH — downloads may fail", RED)

    def _build(self):
        PX = 26

        # Header
        tk.Label(self, text="▶  DOWNLOADER", font=F_TITLE,
                 bg=BG, fg=ACCENT).pack(anchor="w", padx=PX, pady=(26, 0))
        tk.Label(self, text="yt-dlp + ffmpeg", font=F_MONO,
                 bg=BG, fg=FG_DIM).pack(anchor="w", padx=PX, pady=(0, 18))

        self._rule()

        # URL
        self._lbl("URL", PX)
        uf = tk.Frame(self, bg=BG)
        uf.pack(fill="x", padx=PX, pady=(4, 18))
        self._url_entry = tk.Entry(
            uf, textvariable=self._url,
            font=F_MONO, bg=SURFACE, fg=FG,
            insertbackground=ACCENT, relief="flat",
            highlightthickness=1, highlightcolor=ACCENT,
            highlightbackground=BORDER, width=52
        )
        self._url_entry.pack(side="left", ipady=9, ipadx=8, fill="x", expand=True)
        tk.Button(uf, text="✕", font=F_LABEL, bg=SURFACE, fg=FG_DIM,
                  relief="flat", activebackground=BORDER, activeforeground=FG,
                  cursor="hand2", command=lambda: self._url.set("")
                  ).pack(side="left", padx=(4,0), ipady=9, ipadx=8)

        self._rule()

        self._lbl("FORMAT", PX)
        ff = tk.Frame(self, bg=BG)
        ff.pack(fill="x", padx=PX, pady=(8, 18))

        self._fmt_btns = {}
        for val, icon, desc in [
            ("mp4", "▶", "MP4   video + audio"),
            ("mp3", "♪", "MP3   audio only"),
        ]:
            btn = tk.Button(
                ff, text=f"  {icon}  {desc}  ",
                font=F_FMT, relief="flat", cursor="hand2",
                activebackground=ACCENT, activeforeground=BG,
                bd=0, padx=10, pady=10,
                command=lambda v=val: self._pick_fmt(v)
            )
            btn.pack(side="left", padx=(0, 10))
            self._fmt_btns[val] = btn
        self._pick_fmt("mp4") 

        self._rule()


        self._lbl("SAVE TO", PX)
        df = tk.Frame(self, bg=BG)
        df.pack(fill="x", padx=PX, pady=(4, 18))
        tk.Entry(
            df, textvariable=self._dest,
            font=F_MONO, bg=SURFACE, fg=FG,
            insertbackground=CYAN, relief="flat",
            highlightthickness=1, highlightcolor=CYAN,
            highlightbackground=BORDER, width=42
        ).pack(side="left", ipady=9, ipadx=8, fill="x", expand=True)
        tk.Button(df, text="BROWSE", font=F_LABEL, bg=SURFACE, fg=CYAN,
                  relief="flat", activebackground=BORDER, activeforeground=FG,
                  cursor="hand2", command=self._browse
                  ).pack(side="left", padx=(6,0), ipady=9, ipadx=12)

        self._rule()


        pf = tk.Frame(self, bg=BG)
        pf.pack(fill="x", padx=PX, pady=(0, 4))
        s = ttk.Style(self)
        s.theme_use("default")
        s.configure("Y.Horizontal.TProgressbar",
                    troughcolor=SURFACE, background=ACCENT,
                    bordercolor=BORDER, lightcolor=ACCENT, darkcolor=ACCENT,
                    thickness=5)
        ttk.Progressbar(pf, variable=self._pct,
                        style="Y.Horizontal.TProgressbar",
                        mode="determinate", maximum=100
                        ).pack(fill="x")

        self._status_lbl = tk.Label(self, textvariable=self._status,
                                    font=F_MONO, bg=BG, fg=FG_DIM, anchor="w")
        self._status_lbl.pack(fill="x", padx=PX, pady=(2, 8))


        lf = tk.Frame(self, bg=SURFACE, highlightthickness=1,
                      highlightbackground=BORDER)
        lf.pack(fill="x", padx=PX, pady=(0, 0))
        self._txt = tk.Text(lf, height=7, bg=SURFACE, fg=FG_DIM,
                            font=F_MONO, relief="flat", state="disabled",
                            wrap="word")
        sb = tk.Scrollbar(lf, command=self._txt.yview,
                          bg=SURFACE, troughcolor=SURFACE,
                          activebackground=BORDER, relief="flat")
        self._txt.configure(yscrollcommand=sb.set)
        self._txt.pack(side="left", fill="both", expand=True, padx=8, pady=6)
        sb.pack(side="right", fill="y")

        self._rule()


        self._dl_btn = tk.Button(
            self, text="⬇   DOWNLOAD", font=F_BTN,
            bg=ACCENT, fg=BG, relief="flat",
            activebackground="#c8df00", activeforeground=BG,
            cursor="hand2", command=self._start, width=22, pady=10
        )
        self._dl_btn.pack(pady=(0, 26))

    def _rule(self):
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=26, pady=0)

    def _lbl(self, text, px):
        tk.Label(self, text=text, font=F_LABEL, bg=BG, fg=FG_DIM
                 ).pack(anchor="w", padx=px, pady=(12, 0))

    def _pick_fmt(self, val):
        self._fmt.set(val)
        for v, btn in self._fmt_btns.items():
            if v == val:
                btn.configure(bg=ACCENT, fg=BG)
            else:
                btn.configure(bg=SURFACE, fg=FG_DIM)

    def _browse(self):
        p = filedialog.askdirectory(initialdir=self._dest.get())
        if p:
            self._dest.set(p)


    def _log(self, text, color=FG_DIM):
        def _inner():
            self._txt.configure(state="normal")
            tag = f"c{color}"
            self._txt.tag_configure(tag, foreground=color)
            self._txt.insert("end", text + "\n", tag)
            self._txt.see("end")
            self._txt.configure(state="disabled")
        self.after(0, _inner)

    def _setstatus(self, text, color=FG_DIM):
        self.after(0, lambda: (
            self._status.set(text),
            self._status_lbl.configure(fg=color)
        ))

    def _setpct(self, v):
        self.after(0, lambda: self._pct.set(v))

    def _setbusy(self, busy):
        self._busy = busy
        self.after(0, lambda: self._dl_btn.configure(
            state="disabled" if busy else "normal",
            bg=FG_DIM if busy else ACCENT
        ))

    def _start(self):
        if self._busy:
            return
        url = self._url.get().strip()
        if not url:
            messagebox.showwarning("No URL", "Paste a URL first.")
            return
        dest = self._dest.get().strip()
        if not os.path.isdir(dest):
            messagebox.showerror("Bad path", f"Folder not found:\n{dest}")
            return
        self._setbusy(True)
        self._setpct(0)
        self._setstatus("starting…", FG_DIM)
        threading.Thread(target=self._worker,
                         args=(url, dest, self._fmt.get()),
                         daemon=True).start()

    def _worker(self, url, dest, fmt):
        self._log(f"→ {url}", CYAN)
        self._log(f"  {fmt.upper()}  →  {dest}", FG_DIM)

        outtmpl = os.path.join(dest, "%(title)s.%(ext)s")


        base = {
            "outtmpl": outtmpl,
            "progress_hooks": [self._hook],
            "quiet": True,
            "no_warnings": True,
        }
        if FFMPEG_LOCATION is not None:
            base["ffmpeg_location"] = FFMPEG_LOCATION

        if fmt == "mp3":
            opts = {
                **base,
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            }
        else:
            opts = {
                **base,
                "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "merge_output_format": "mp4",
            }

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get("title", "file")
            self._setpct(100)
            self._setstatus(f"done: {title}", GREEN)
            self._log(f"✓  {title}", GREEN)
        except Exception as e:
            msg = strip(str(e))
            self._setstatus("error — see log", RED)
            self._log(f"✗  {msg}", RED)
        finally:
            self._setbusy(False)

    def _hook(self, d):
        if d["status"] == "downloading":
            pct   = strip(d.get("_percent_str", "0%")).strip().rstrip("%")
            speed = strip(d.get("_speed_str",   "…")).strip()
            eta   = strip(d.get("_eta_str",     "…")).strip()
            try:
                self._setpct(float(pct))
            except ValueError:
                pass
            self._setstatus(f"{pct}%   {speed}/s   ETA {eta}", ACCENT)
        elif d["status"] == "finished":
            self._setstatus("processing…", CYAN)
            self._log("  ↳ converting…", FG_DIM)


if __name__ == "__main__":
    App().mainloop()
