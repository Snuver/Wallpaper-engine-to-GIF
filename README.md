# Wallpaper GIF Converter

### Made by Snuver

I made this because somehow converting Wallpaper Engine stuff into a normal GIF is way more annoying than it should be lol.

---

# Tutorial

First, install whatever Wallpaper Engine background you want to convert.

Right click the wallpaper in Wallpaper Engine:

<img width="610" height="750" alt="Wallpaper Engine right click menu" src="https://github.com/user-attachments/assets/87757d67-5112-47fe-a010-9c539a7f6d6d" />

Click **Open in Explorer**.

Once File Explorer opens, go back **one folder** so the wallpaper folder itself is selected.

Then click the **three dots** at the top and choose **Compress to ZIP file**.

<img width="356" height="744" alt="Compress wallpaper folder" src="https://github.com/user-attachments/assets/ed5ba091-94be-4e9c-871f-1dbe08d0ca24" />

Now you should have a ZIP of the wallpaper.

Drag that ZIP onto:

```text
WE-To-GIF.bat
```

<img width="2536" height="1494" alt="image (3)" src="https://github.com/user-attachments/assets/3754d877-4f0a-4918-b76f-120badaad561" />

The converter will ask for your GIF length, FPS, width, and target file size.

If you do not care about the settings, you can just press **ENTER** and use the recommended ones.

Then let it do its thing lol.


You can also give it a Wallpaper Engine folder, `project.json`, or a normal video file.

---

### Video wallpaper?

Easy. It just converts the video.

### Scene wallpaper?

It makes Wallpaper Engine render the scene, records the actual visible wallpaper area, then turns that recording into a GIF.

---

# Why does it record the screen area?

Because Wallpaper Engine is GPU rendered and normal window capture can literally record a black box even while the wallpaper looks perfectly fine on your screen.

So yeah.

Desktop region capture it is 😭

---

# How to use it

1. Extract the converter folder.
2. Get the Wallpaper Engine wallpaper you want.
3. Compress the wallpaper folder into a ZIP.
4. Drag the ZIP onto `WE-To-GIF-v1.5.bat`.
5. Choose your GIF length, FPS, width, and target file size.
6. If you do not care, just press ENTER and use the recommended settings.
7. Do **NOT** cover or minimize the Wallpaper Engine pop-out while it records.
8. Done.

---

# Recommended settings

For a normal GIF I usually recommend:

- **Length:** 10 seconds
- **FPS:** 12
- **Width:** 1280 px
- **Target size:** 5 MB

You can absolutely use **30 FPS** if you want.

Just know GIF is an ancient format and file sizes can get stupidly huge really fast 😭

The converter tries to optimize the GIF automatically and keep it under your target size without completely destroying the quality.

---

# Where is my GIF?

Finished GIFs automatically go here:

```text
C:\Users\YOUR_NAME\Videos\Wallpaper GIF Converter\
```

So you do not have to go digging through your Steam folders looking for it lol.

---

# Supported right now

- Wallpaper Engine Scene wallpapers
- Wallpaper Engine Video wallpapers
- Normal video files
- Wallpaper Engine ZIP files
- Wallpaper Engine folders
- `project.json`
- Custom GIF length
- Custom FPS
- Custom resolution
- Custom target file size
- Automatic FFmpeg detection/download
- Automatic GIF file size optimization

---

# Not supported yet

- Web wallpapers

I'll probably add more stuff later if I feel like suffering.

---

# How Scene wallpapers work

Basically:

```text
Wallpaper Engine Scene
        ↓
Wallpaper Engine renders it
        ↓
Converter finds the actual wallpaper area
        ↓
Records it
        ↓
FFmpeg turns it into a GIF
        ↓
Optimizer tries to keep the file size sane
        ↓
Done
```

Wallpaper Engine itself is still doing the actual Scene rendering.

The converter just handles everything around it.

---

# Requirements

For Scene wallpapers:

- Windows
- Wallpaper Engine
- Python
- FFmpeg

If FFmpeg is missing, the converter can download it automatically.

---

# Credit

Made by **ME!!!! SNUVA!!**

aka **Snuver**

If you share it, modify it, or make something based on it, keeping the credit wooould be nicee 👀

---

### Made by Snuver
