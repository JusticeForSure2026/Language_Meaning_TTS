import sys
import threading
import pythoncom
import pyttsx3
from PySide6.QtWidgets import (
    QApplication, QWidget, QTextEdit, QVBoxLayout, QPushButton, QLabel, QComboBox, QHBoxLayout, QLineEdit, QSizePolicy
)
from PySide6.QtCore import Signal, QObject
from PySide6.QtGui import QTextCursor, QColor, QIcon

import os
import shutil
import wave
import subprocess


class PlainTextEdit(QTextEdit):
    def insertFromMimeData(self, source):
        self.insertPlainText(source.text())


class WorkerSignals(QObject):
    lineChanged = Signal(int, str)
    finished = Signal()


class TTSWorker(threading.Thread):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.voice_id1 = ""
        self.voice_id2 = ""

        self.last_target_edit = None
        self.last_position = 0
        self.last_length = 0
        self.last_background = None

        self._pause_event = threading.Event()
        self._stop_event = threading.Event()

    def pause(self):
        self._pause_event.clear()

    def resume(self):
        self._pause_event.set()

    def stop(self):
        self._stop_event.set()
        self._pause_event.set()

    def run(self):
        pythoncom.CoInitialize()
        total_lines = len(self.app.text1)

        while self.app.current_index < total_lines and not self._stop_event.is_set():
            while not self._pause_event.is_set() and not self._stop_event.is_set():
                pass

            self.app.signals.lineChanged.emit(self.app.current_index, "left")

            self.app.engine = pyttsx3.init()
            self.app.engine.setProperty('voice', self.voice_id1)
            self.app.engine.setProperty('rate', self.app.current_speed)
            self.app.engine.say(self.app.text1[self.app.current_index])
            self.app.engine.runAndWait()
            self.app.engine = None

            self.app.signals.lineChanged.emit(self.app.current_index, "right")

            self.app.engine = pyttsx3.init()
            self.app.engine.setProperty('voice', self.voice_id2)
            self.app.engine.setProperty('rate', self.app.current_speed)
            self.app.engine.say(self.app.text2[self.app.current_index])
            self.app.engine.runAndWait()
            self.app.engine = None

            self.app.current_index += 1

        self.app.signals.finished.emit()


class TTSApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Language Meaning TTS")
        self.resize(800, 600)

        self.voices = pyttsx3.init().getProperty('voices')
        self.voice_string_list = [item.id for item in self.voices]
        self.voice_name_list = [item.name for item in self.voices]

        # self.voice_name_list = None

        self.layout = QVBoxLayout(self)

        language_global_layout = QHBoxLayout()

        # Language 1 voice selection
        language_vertical_layout1 = QVBoxLayout()

        voice_layout = QHBoxLayout()
        self.voice_label = QLabel("First Voice:")
        voice_layout.addWidget(self.voice_label)

        self.voice_combo1 = QComboBox()

        self.voice_combo1.addItems(self.voice_name_list)

        self.voice_combo1.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.voice_combo1.currentIndexChanged.connect(self.on_voice_change)
        voice_layout.addWidget(self.voice_combo1)

        self.font_combo1 = QComboBox()
        self.font_options = ["aaa", "Aa", "AA"]
        self.font_sizes = [9, 12, 16]
        self.font_combo1.addItems(self.font_options)
        self.font_combo1.setFixedWidth(80)
        self.font_combo1.currentIndexChanged.connect(self.change_font_size1)
        voice_layout.addWidget(self.font_combo1)

        language_vertical_layout1.addLayout(voice_layout)

        # Text edit 1
        self.text_edit1 = PlainTextEdit()
        language_vertical_layout1.addWidget(self.text_edit1)
        self.original_background1 = self.text_edit1.palette().base().color()
        self.text_edit1.textChanged.connect(self.text_changed)

        language_global_layout.addLayout(language_vertical_layout1)

        # Language 2 voice selection
        language_vertical_layout2 = QVBoxLayout()

        voice_layout = QHBoxLayout()
        self.voice_label = QLabel("Second Voice:")
        voice_layout.addWidget(self.voice_label)

        self.voice_combo2 = QComboBox()

        self.voice_combo2.addItems(self.voice_name_list)

        self.voice_combo2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.voice_combo2.currentIndexChanged.connect(self.on_voice_change)
        voice_layout.addWidget(self.voice_combo2)

        self.font_combo2 = QComboBox()
        self.font_options = ["aaa", "Aa", "AA"]
        self.font_sizes = [9, 12, 16]
        self.font_combo2.addItems(self.font_options)
        self.font_combo2.setFixedWidth(80)
        self.font_combo2.currentIndexChanged.connect(self.change_font_size2)
        voice_layout.addWidget(self.font_combo2)

        language_vertical_layout2.addLayout(voice_layout)

        # Text edit 2
        self.text_edit2 = PlainTextEdit()
        language_vertical_layout2.addWidget(self.text_edit2)
        self.original_background2 = self.text_edit2.palette().base().color()
        self.text_edit2.textChanged.connect(self.text_changed)

        language_global_layout.addLayout(language_vertical_layout2)

        self.layout.addLayout(language_global_layout)

        # Controls
        control_layout = QHBoxLayout()

        self.play_btn = QPushButton("▶️ Play")
        self.play_btn.clicked.connect(self.toggle_play)
        control_layout.addWidget(self.play_btn)

        control_layout.addWidget(QLabel("Speed:"))
        self.speed_edit = QLineEdit("1.0")
        control_layout.addWidget(self.speed_edit)
        self.speed_edit.textChanged.connect(self.update_speed)

        self.save_btn = QPushButton("💾 Save")
        self.save_btn.clicked.connect(self.save_file)
        control_layout.addWidget(self.save_btn)

        self.layout.addLayout(control_layout)

        # TTS worker
        self.worker = None
        self.signals = WorkerSignals()
        self.signals.lineChanged.connect(self.highlight_line)
        self.signals.finished.connect(self.on_finished)

        self.engine = None
        self.is_playing = False
        self.speed_factor = 1.0
        self.current_speed = 200
        self.lines = []
        self.text_modified = True
        self.current_index = 0

    def on_voice_change(self, index):
        if self.worker:
            self.worker.voice_id1 = self.voice_string_list[index]

    def change_font_size1(self, index):
        font = self.text_edit1.font()
        font.setPointSize(self.font_sizes[index])
        self.text_edit1.setFont(font)

    def change_font_size2(self, index):
        font = self.text_edit2.font()
        font.setPointSize(self.font_sizes[index])
        self.text_edit2.setFont(font)

    def update_speed(self):
        try:
            self.speed_factor = float(self.speed_edit.text())
        except ValueError:
            self.speed_factor = 1.0

        self.current_speed = int(200 * self.speed_factor)

    def toggle_play(self):
        text_lines = self.text_edit1.toPlainText().splitlines()
        if self.text_modified or not self.lines:
            self.lines = text_lines
            self.text_modified = False
            self.current_index = 0

        if not self.lines:
            return

        if not self.is_playing:
            self.worker = TTSWorker(self)
            self.worker.voice_id1 = self.voice_string_list[self.voice_combo1.currentIndex()]
            self.worker.voice_id2 = self.voice_string_list[self.voice_combo2.currentIndex()]
            self.worker._pause_event.set()
            self.worker.start()
            self.is_playing = True
            self.play_btn.setText("⏸️ Pause")
        else:
            if self.worker._pause_event.is_set():
                self.worker.pause()
                self.play_btn.setText("▶️ Play")

                self.engine.stop()
                if self.current_index > 0:
                    self.current_index -= 1
            else:
                self.worker.resume()
                self.play_btn.setText("⏸️ Pause")

    def on_finished(self):
        self.is_playing = False
        self.play_btn.setText("▶️ Play")
        self.current_index = 0

    def highlight_line(self, idx, side):
        last_target_edit = getattr(self, 'last_target_edit', None)

        if last_target_edit is not None:
            last_target_edit.blockSignals(True)
            prev_cursor = last_target_edit.textCursor()

            last_position = getattr(self, 'last_position', 0)
            last_length = getattr(self, 'last_length', 0)
            last_background = getattr(self, 'last_background', None)

            prev_cursor.setPosition(last_position)
            prev_cursor.setPosition(last_position + last_length, QTextCursor.KeepAnchor)
            last_target_edit.setTextCursor(prev_cursor)
            last_target_edit.setTextBackgroundColor(last_background)

            prev_cursor.clearSelection()
            last_target_edit.setTextCursor(prev_cursor)
            last_target_edit.blockSignals(False)

        if side == "left":
            target_edit = self.text_edit1
            lines_pool = self.text1
            current_bg = self.original_background1
        else:
            target_edit = self.text_edit2
            lines_pool = self.text2
            current_bg = self.original_background2

        if idx >= len(lines_pool):
            return

        pos = 0
        for i in range(idx):
            pos += len(lines_pool[i]) + 1
        line_len = len(lines_pool[idx])

        target_edit.blockSignals(True)
        cursor = target_edit.textCursor()

        cursor.setPosition(pos)
        cursor.setPosition(pos + line_len, QTextCursor.KeepAnchor)
        target_edit.setTextCursor(cursor)
        target_edit.setTextBackgroundColor(QColor("green"))

        target_edit.ensureCursorVisible()

        cursor.clearSelection()
        target_edit.setTextCursor(cursor)
        target_edit.blockSignals(False)

        self.last_target_edit = target_edit
        self.last_position = pos
        self.last_length = line_len
        self.last_background = current_bg

    def save_file(self):
        self.save_btn.setEnabled(False)
        self.save_btn.setText("⏳ Saving")

        QApplication.processEvents()

        try:
            current_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()

            # 建立臨時資料夾
            dir1 = os.path.join(current_dir, "FirstVoiceTemporary")
            dir2 = os.path.join(current_dir, "SecondVoiceTemporary")
            for folder in [dir1, dir2]:
                if os.path.exists(folder):
                    shutil.rmtree(folder)
                os.makedirs(folder, exist_ok=True)

            # 處理全文 / 置換為 , 並切行
            text1_lines = self.text_edit1.toPlainText().replace("/", ",").splitlines()
            text2_lines = self.text_edit2.toPlainText().replace("/", ",").splitlines()

            max_len = max(len(text1_lines), len(text2_lines))
            text1_lines += [""] * (max_len - len(text1_lines))
            text2_lines += [""] * (max_len - len(text2_lines))

            voice_id1 = self.voice_string_list[self.voice_combo1.currentIndex()]
            voice_id2 = self.voice_string_list[self.voice_combo2.currentIndex()]

            wav_files = []

            # 逐行交替錄音
            for idx, (f_line, c_line) in enumerate(zip(text1_lines, text2_lines), 1):
                if f_line.strip():
                    f_wav = os.path.join(dir1, f"F{idx}.wav")
                    engine_f = pyttsx3.init()
                    engine_f.setProperty("voice", voice_id1)
                    engine_f.save_to_file(f_line, f_wav)
                    engine_f.runAndWait()
                    engine_f.stop()
                    del engine_f
                    wav_files.append(f_wav)

                if c_line.strip():
                    s_wav = os.path.join(dir2, f"S{idx}.wav")
                    engine_c = pyttsx3.init()
                    engine_c.setProperty("voice", voice_id2)
                    engine_c.save_to_file(c_line, s_wav)
                    engine_c.runAndWait()
                    engine_c.stop()
                    del engine_c
                    wav_files.append(s_wav)

            if not wav_files:
                return

            # 合併 WAV 音檔
            combined_path = os.path.join(current_dir, "Combined.wav")
            data = []
            params = None
            for wav_file in wav_files:
                with wave.open(wav_file, 'rb') as w:
                    if params is None:
                        params = w.getparams()
                    data.append(w.readframes(w.getnframes()))

            with wave.open(combined_path, 'wb') as out:
                out.setparams(params)
                for frames in data:
                    out.writeframes(frames)

            # ----------------------------------------------------
            # ✨ 核心改動：自動識別打包路徑 (直接複製貼上，不要改動)
            # ----------------------------------------------------
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = current_dir

            if sys.platform == "win32":
                ffmpeg_path = os.path.join(base_path, "ffmpeg-8.0-essentials_build", "bin", "ffmpeg.exe")
            else:
                ffmpeg_path = os.path.join(base_path, "ffmpeg-8.0-essentials_build", "bin", "ffmpeg")

            try:
                speed_val = float(self.speed_edit.text())
            except ValueError:
                speed_val = 1.0

            output_ogg = os.path.join(current_dir, "Combined.ogg")

            subprocess.run([
                ffmpeg_path,
                "-y",
                "-i", combined_path,
                "-filter:a", f"atempo={speed_val}",
                output_ogg
            ])

            if os.path.exists(combined_path):
                os.remove(combined_path)
            for folder in [dir1, dir2]:
                if os.path.exists(folder):
                    shutil.rmtree(folder)

        finally:
            self.save_btn.setEnabled(True)
            self.save_btn.setText("💾 Save")

    def closeEvent(self, event):
        if self.worker:
            self.worker.stop()
        event.accept()

    def text_changed(self):
        self.text_modified = True
        self.text1 = self.text_edit1.toPlainText().replace("/", ",").splitlines()
        self.text2 = self.text_edit2.toPlainText().replace("/", ",").splitlines()
        self.current_index = 0


if __name__ == "__main__":
    app = QApplication(sys.argv)

    if getattr(sys, 'frozen', False):
        base_icon_path = sys._MEIPASS
    else:
        base_icon_path = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()

    if sys.platform == "win32":
        icon_path = os.path.join(base_icon_path, "language_meaning-tts_icon.ico")
        app.setWindowIcon(QIcon(icon_path))

    elif sys.platform == "darwin":
        icon_path = os.path.join(base_icon_path, "language_meaning-tts_icon.png")
        app.setWindowIcon(QIcon(icon_path))

    window = TTSApp()
    window.show()
    sys.exit(app.exec())
