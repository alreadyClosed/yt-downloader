# YT-Downloader

downloads videos and audio from youtube and pretty much anywhere else yt-dlp supports. outputs mp4 or mp3, you pick.

---

## what you need

- **Python 3.10+** - https://python.org/downloads (check "Add to PATH" during install)
- **ffmpeg** - https://ffmpeg.org/download.html, grab the windows build, extract it somewhere like `C:\ffmpeg`, then add `C:\ffmpeg\bin` to your system PATH
- **yt-dlp** - installed via pip (see below)

---

## setup (one time)

**1. install yt-dlp**

open a terminal and run:

```
pip install yt-dlp
```

**2. make sure ffmpeg works**

open a new terminal and type:

```
ffmpeg -version
```

if it prints version info you're good. if it says "not found", the `bin` folder isn't on your PATH yet, see the ffmpeg note above.

---

## running it

double-click `YoutubeDownloader.vbs`

if that doesn't work for some reason, you can also just do:

```
python downloader.py
```

---

## usage

1. paste a URL
2. pick MP4 for video or MP3 for audio only
3. choose where to save it
4. hit download

---

## notes

- MP3 exports at 192kbps
- MP4 grabs the best available video + audio and merges them, which is why ffmpeg is required
- if a download fails, the log box at the bottom usually tells you why
