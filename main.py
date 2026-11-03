import sys
import struct
import threading
import pythoncom
import pyttsx3
from PySide6.QtWidgets import (
    QApplication, QWidget, QTextEdit, QVBoxLayout, QPushButton, QLabel, QComboBox, QHBoxLayout, QLineEdit, QSizePolicy,
    QSpinBox, QCheckBox
)
from PySide6.QtCore import Signal, QObject
from PySide6.QtGui import QTextCursor, QColor, QIcon
import time

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

        self.single_language_only = False

        self.repetition_times1 = 1
        self.repetition_times2 = 1

        self.pause1 = 0.0
        self.pause2 = 0.0

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

            for i in range(self.repetition_times1):
                self.app.engine = pyttsx3.init()
                self.app.engine.setProperty('voice', self.voice_id1)
                self.app.engine.setProperty('rate', self.app.current_speed)
                self.app.engine.say(self.app.text1[self.app.current_index])
                self.app.engine.runAndWait()
                self.app.engine = None

                counter = 0
                start_time = time.time()
                while (time.time() - start_time) < self.pause1:
                    counter += 1

            if not self.single_language_only:
                self.app.signals.lineChanged.emit(self.app.current_index, "right")

                for i in range(self.repetition_times2):
                    self.app.engine = pyttsx3.init()
                    self.app.engine.setProperty('voice', self.voice_id2)
                    self.app.engine.setProperty('rate', self.app.current_speed)
                    self.app.engine.say(self.app.text2[self.app.current_index])
                    self.app.engine.runAndWait()
                    self.app.engine = None

                    counter = 0
                    start_time = time.time()
                    while (time.time() - start_time) < self.pause2:
                        counter += 1

            self.app.current_index += 1

        self.app.signals.finished.emit()


class TTSApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Language Meaning TTS")
        self.resize(960, 640)

        self.voices = pyttsx3.init().getProperty('voices')
        self.voice_string_list = [item.id for item in self.voices]
        self.voice_name_list = [item.name for item in self.voices]

        self.layout = QVBoxLayout(self)

        description_label = QLabel(
            "<b>When outputting audio files, the system will generate:</b><br>"
            "• <code>FirstVoiceTemporary12345</code> folder<br>"
            "• <code>SecondVoiceTemporary12345</code> folder<br>"
            "• <code>SilentTemporary12345.wav</code><br>"
            "<font color='#2980B9'><b>Note:</b> Avoid renaming any of your personal files to the names above "
            "to prevent your personal data from being deleted.</font>"
        )
        self.layout.addWidget(description_label)

        self.single_language_checkbox = QCheckBox("Single language only")
        self.single_language_checkbox.stateChanged.connect(self.on_single_language_checkbox_changed)
        self.layout.addWidget(self.single_language_checkbox)

        language_global_layout = QHBoxLayout()
        language_global_layout.setContentsMargins(0, 4, 0, 0)

        # Language 1 voice selection
        language_vertical_layout1 = QVBoxLayout()
        language_vertical_layout1.setContentsMargins(0, 0, 0, 10)

        voice_layout = QHBoxLayout()
        voice_label = QLabel("First Voice:")
        voice_layout.addWidget(voice_label)

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

        repetition_layout1 = QHBoxLayout()

        repetition_label1 = QLabel("Repeat: ")
        repetition_layout1.addWidget(repetition_label1)

        self.repetition_spinbox1 = QSpinBox()
        self.repetition_spinbox1.setRange(1, 100)
        self.repetition_spinbox1.setValue(1)
        self.repetition_spinbox1.setFixedWidth(100)
        repetition_layout1.addWidget(self.repetition_spinbox1)

        repetition_label2 = QLabel(" times")
        repetition_layout1.addWidget(repetition_label2)

        repetition_layout1.addStretch(1)
        language_vertical_layout1.addLayout(repetition_layout1)

        pause_layout1 = QHBoxLayout()

        repetition_label3 = QLabel("Pause: ")
        pause_layout1.addWidget(repetition_label3)

        self.pause_edit1 = QLineEdit("0.0")
        self.pause_edit1.textChanged.connect(self.update_pause1)
        pause_layout1.addWidget(self.pause_edit1)

        repetition_label4 = QLabel(" seconds - each line")
        pause_layout1.addWidget(repetition_label4)

        pause_layout1.addStretch(1)
        language_vertical_layout1.addLayout(pause_layout1)

        # Text edit 1
        self.text_edit1 = PlainTextEdit()
        language_vertical_layout1.addWidget(self.text_edit1)
        self.original_background1 = self.text_edit1.palette().base().color()
        self.text_edit1.textChanged.connect(self.text_changed)

        language_global_layout.addLayout(language_vertical_layout1)

        # Language 2 voice selection
        self.language_vertical_layout_widget2 = QWidget()
        language_vertical_layout2 = QVBoxLayout(self.language_vertical_layout_widget2)
        language_vertical_layout2.setContentsMargins(10, 0, 0, 10)

        voice_layout = QHBoxLayout()
        voice_label = QLabel("Second Voice:")
        voice_layout.addWidget(voice_label)

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

        repetition_layout2 = QHBoxLayout()

        repetition_label5 = QLabel("Repeat: ")
        repetition_layout2.addWidget(repetition_label5)

        self.repetition_spinbox2 = QSpinBox()
        self.repetition_spinbox2.setRange(1, 100)
        self.repetition_spinbox2.setValue(1)
        self.repetition_spinbox2.setFixedWidth(100)
        repetition_layout2.addWidget(self.repetition_spinbox2)

        repetition_label6 = QLabel(" times")
        repetition_layout2.addWidget(repetition_label6)

        repetition_layout2.addStretch(1)
        language_vertical_layout2.addLayout(repetition_layout2)

        pause_layout2 = QHBoxLayout()

        repetition_label7 = QLabel("Pause: ")
        pause_layout2.addWidget(repetition_label7)

        self.pause_edit2 = QLineEdit("0.0")
        self.pause_edit2.textChanged.connect(self.update_pause2)
        pause_layout2.addWidget(self.pause_edit2)

        repetition_label8 = QLabel(" seconds - each line")
        pause_layout2.addWidget(repetition_label8)

        pause_layout2.addStretch(1)
        language_vertical_layout2.addLayout(pause_layout2)

        # Text edit 2
        self.text_edit2 = PlainTextEdit()
        language_vertical_layout2.addWidget(self.text_edit2)
        self.original_background2 = self.text_edit2.palette().base().color()
        self.text_edit2.textChanged.connect(self.text_changed)

        language_global_layout.addWidget(self.language_vertical_layout_widget2)

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

    def on_single_language_checkbox_changed(self, state):
        if state == 2:
            self.language_vertical_layout_widget2.hide()
        else:
            self.language_vertical_layout_widget2.show()

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
            self.speed_edit.setText("1.0")
            self.speed_factor = 1.0

        self.current_speed = int(200 * self.speed_factor)

    def update_pause1(self):
        try:
            test_number = 0.0
            test_number = float(self.pause_edit1.text())
        except ValueError:
            self.pause_edit1.setText("0.0")

    def update_pause2(self):
        try:
            test_number = 0.0
            test_number = float(self.pause_edit2.text())
        except ValueError:
            self.pause_edit2.setText("0.0")

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

            self.worker.single_language_only = self.single_language_checkbox.isChecked()

            self.worker.repetition_times1 = self.repetition_spinbox1.value()
            self.worker.repetition_times2 = self.repetition_spinbox2.value()

            try:
                self.worker.pause1 = round(float(self.pause_edit1.text()), 1)
            except ValueError:
                self.worker.pause1 = 0.0

            try:
                self.worker.pause2 = round(float(self.pause_edit2.text()), 1)
            except ValueError:
                self.worker.pause2 = 0.0

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

        self.generate_01s_silent_wav()
        silent_01s_path = "SilentTemporary12345.wav"

        QApplication.processEvents()

        try:
            current_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()

            dir1 = os.path.join(current_dir, "FirstVoiceTemporary12345")
            dir2 = os.path.join(current_dir, "SecondVoiceTemporary12345")
            for folder in [dir1, dir2]:
                if os.path.exists(folder):
                    shutil.rmtree(folder)
                os.makedirs(folder, exist_ok=True)

            text1_lines = self.text_edit1.toPlainText().replace("/", ",").splitlines()
            text2_lines = self.text_edit2.toPlainText().replace("/", ",").splitlines()

            max_len = max(len(text1_lines), len(text2_lines))
            text1_lines += [""] * (max_len - len(text1_lines))
            text2_lines += [""] * (max_len - len(text2_lines))

            voice_id1 = self.voice_string_list[self.voice_combo1.currentIndex()]
            voice_id2 = self.voice_string_list[self.voice_combo2.currentIndex()]

            wav_files = []

            # Calculate the time of pause 1
            pause_duration1 = 0.0
            try:
                pause_duration1 = round(float(self.pause_edit1.text()), 1)
            except ValueError:
                pause_duration1 = 0.0

            repetition_count1 = int(pause_duration1 / 0.1)

            if self.single_language_checkbox.isChecked():
                for idx, f_line in enumerate(text1_lines, 1):
                    if f_line.strip():
                        for index in range(self.repetition_spinbox1.value()):
                            f_wav = os.path.join(dir1, f"F{idx}_{index}.wav")
                            engine_f = pyttsx3.init()
                            engine_f.setProperty("voice", voice_id1)
                            engine_f.save_to_file(f_line, f_wav)
                            engine_f.runAndWait()
                            engine_f.stop()
                            del engine_f
                            wav_files.append(f_wav)

                            for i in range(repetition_count1):
                                wav_files.append(silent_01s_path)
            else:
                # Calculate the time of pause 2
                pause_duration2 = 0.0
                try:
                    pause_duration2 = round(float(self.pause_edit2.text()), 1)
                except ValueError:
                    pause_duration2 = 0.0

                repetition_count2 = int(pause_duration2 / 0.1)

                for idx, (f_line, c_line) in enumerate(zip(text1_lines, text2_lines), 1):
                    if f_line.strip():

                        for index in range(self.repetition_spinbox1.value()):
                            f_wav = os.path.join(dir1, f"F{idx}_{index}.wav")
                            engine_f = pyttsx3.init()
                            engine_f.setProperty("voice", voice_id1)
                            engine_f.save_to_file(f_line, f_wav)
                            engine_f.runAndWait()
                            engine_f.stop()
                            del engine_f
                            wav_files.append(f_wav)

                            for i in range(repetition_count1):
                                wav_files.append(silent_01s_path)

                    if c_line.strip():
                        for index in range(self.repetition_spinbox2.value()):
                            s_wav = os.path.join(dir2, f"S{idx}_{index}.wav")
                            engine_c = pyttsx3.init()
                            engine_c.setProperty("voice", voice_id2)
                            engine_c.save_to_file(c_line, s_wav)
                            engine_c.runAndWait()
                            engine_c.stop()
                            del engine_c
                            wav_files.append(s_wav)

                            for i in range(repetition_count2):
                                wav_files.append(silent_01s_path)

            if not wav_files:
                return

            # Combine wav
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

            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = current_dir

            if sys.platform == "win32":
                ffmpeg_path = os.path.join(base_path, "ffmpeg-8.0-essentials_build", "bin", "ffmpeg.exe")
            else:
                ffmpeg_path = os.path.join(base_path, "ffmpeg-8.0-essentials_build", "bin", "ffmpeg")

            try:
                speed_value = float(self.speed_edit.text())
            except ValueError:
                speed_value = 1.0

            output_ogg = os.path.join(current_dir, "Combined.ogg")

            subprocess.run([
                ffmpeg_path,
                "-y",
                "-i", combined_path,
                "-filter:a", f"atempo={speed_value}",
                output_ogg
            ])

            if os.path.exists(combined_path):
                os.remove(combined_path)
            for folder in [dir1, dir2]:
                if os.path.exists(folder):
                    shutil.rmtree(folder)

            if os.path.exists(silent_01s_path):
                os.remove(silent_01s_path)

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

    def generate_01s_silent_wav(self):
        output_path = "SilentTemporary12345.wav"

        num_samples = int(22050 * 0.1)

        silent_data = struct.pack('<' + 'h' * num_samples, *(0 for _ in range(num_samples)))

        with wave.open(output_path, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(22050)
            wav_file.writeframes(silent_data)


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
