# Language Meaning TTS

A multi-language audio tool designed for language learners to memorize vocabulary.

Traditional TTS only read words in one language, forcing you to stare at a screen or a book. Language Meaning TTS bridges the gap by creating an instant, sequential audio reflex in your brain.

## 🎯 Core Concept & The Brain Reflex Method

Language Meaning TTS creates an audio reflex by playing your familiar language first, followed immediately by the foreign pronunciation. 

### 🎧 How the Audio Flow Works (Examples)

* **English speaker learning French:**
  > 🔊`"abandon"` ➔ ⏱️ *Pause* ➔ `"abandonner, renoncer"`<br>
  > 🔊`"escape"` ➔ ⏱️ *Pause* ➔ `"s'echapper, fuir"`<br>
  > 🔊`"finish"` ➔ ⏱️ *Pause* ➔ `"finir, achever"`

* **Spanish speaker learning Italian:**
  > 🔊 `"sueño"` ➔ ⏱️ *Pause* ➔ `"il sogno"`<br>
  > 🔊 `"escapar"` ➔ ⏱️ *Pause* ➔ `"scappare"`<br>
  > 🔊 `"terminar"` ➔ ⏱️ *Pause* ➔ `"finire"`

### ⚙️ Practical Design & Workflow
1. **Audio-First Learning:** Listen to your vocabulary anytime, anywhere without staring at a screen.
2. **Instant Mapping:** Hear the meaning right before the foreign word to link them together.
3. **Continuous Playback:** Converts your text list into a single audio file for non-stop listening.

## ✨ Technical Features

* **100% Offline & Free:** This tool runs completely on your local system. It consumes zero online tokens or internet data.
* **Any Two Languages:** Dual drop-down lists let you pick and combine any two languages installed on your operating system.
* **Easy Setup:** Just run the EXE, copy your vocabulary from your list, select your voices, and generate your custom audio instantly.

## 🌐 System Voice Setup & Troubleshooting

The program uses the built-in voice engines already installed on your operating system. 

### If a language is missing from the dropdown list:
1. Open Windows **Settings** (`Win + I`).
2. Go to **Time & language** ➔ **Language & region**.
3. Under **Preferred languages**, click **Add a language**.
4. Search for your target language (e.g., French, Spanish, German) and make sure **Text-to-speech** is enabled.
5. Click **Install**, then restart the application to automatically load the new voice.

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
