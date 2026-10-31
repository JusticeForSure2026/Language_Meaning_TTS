# Language Meaning TTS

A multi-language audio tool designed for language learners to memorize vocabulary.

## ✨ Features

* **Unlimited use:** This TTS tool runs 100% offline and does not consume any online tokens or data. You can generate and play the audio as many times as you want for free.
* **Dual drop-down lists for language selection:** You can pick any two installed languages on your system via dropdown lists to match them together.
* **Combined audio output:** It generates a single, combined audio file matching the foreign language word directly with its meaning in your familiar language for continuous listening.

### Examples:
* **An English speaker learning French:**
  * "dream, le rêve"
  * "escape, s'échapper"
  * "finish, finir"

* **A Spanish speaker learning Italian:**
  * "sueño, il sogno"
  * "escapar, scappare"
  * "terminar, finire"

---

## 🌐 System Voice Setup & Troubleshooting

The program uses the built-in voice engines already installed on your operating system. 

### If a language is missing from the dropdown list:
1. Open Windows **Settings** (`Win + I`).
2. Go to **Time & language** ➔ **Language & region**.
3. Under **Preferred languages**, click **Add a language**.
4. Search for your target language (e.g., French, Spanish, German) and make sure **Text-to-speech** is enabled.
5. Click **Install**, then restart the application to automatically load the new voice.

---

## 📥 How to Use (Choose Your Option)

### Option 1: If you just want to study by yourself
You do not need to download the full source code. Simply download `Language Meaning TTS.exe` under the `executable` folder and run it directly. 

> ℹ️ **Note:** Currently optimized and fully tested for Windows. The macOS version is cross-platform capable but remains untested on native hardware.

### Option 2: If you want to modify or compile the program 

🧑‍💻 Compile the executable file on Windows:
1. Open your terminal in the project root directory and run:
```bash
python -m PyInstaller --clean --noconsole --onefile --icon=language_meaning-tts_icon.png --hidden-import=pyttsx3.drivers --hidden-import=comtypes --add-data "language_meaning-tts_icon.png;." --add-data "ffmpeg-8.0-essentials_build/bin/ffmpeg.exe;ffmpeg-8.0-essentials_build/bin" main.py
```
2. Find your standalone application in the `dist` folder.

<br>

💻 Compile the executable file on Mac:
1. Open your terminal in the project root directory and run:
```bash
python -m PyInstaller --clean --noconsole --onefile --icon=language_meaning-tts_icon.png --hidden-import=pyttsx3.drivers --hidden-import=comtypes --add-data "language_meaning-tts_icon.png;." --add-data "ffmpeg-8.0-essentials_build/bin/ffmpeg.exe;ffmpeg-8.0-essentials_build/bin" main.py
```
2. Find your standalone application in the `dist` folder.
