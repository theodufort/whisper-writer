import time
import traceback
from collections import deque
from threading import Event

import numpy as np
import sounddevice as sd
import webrtcvad
from PyQt5.QtCore import QMutex, QThread, pyqtSignal

from transcription import transcribe
from utils import ConfigManager


class ResultThread(QThread):
    """
    A thread class for handling audio recording, transcription, and result processing.

    This class manages the entire process of:
    1. Recording audio from the microphone
    2. Detecting speech and silence
    3. Saving the recorded audio as numpy array
    4. Transcribing the audio
    5. Emitting the transcription result

    Signals:
        statusSignal: Emits the current status of the thread
            (e.g., 'recording', 'transcribing', 'idle')
        resultSignal: Emits the transcription result
    """

    statusSignal = pyqtSignal(str)
    resultSignal = pyqtSignal(str)

    def __init__(self, local_model=None):
        """
        Initialize the ResultThread.

        :param local_model: Local transcription model (if applicable)
        """
        super().__init__()
        self.local_model = local_model
        self.is_recording = False
        self.is_running = True
        self.sample_rate = None
        self.mutex = QMutex()

    def stop_recording(self):
        """Stop the current recording session."""
        self.mutex.lock()
        self.is_recording = False
        self.mutex.unlock()

    def stop(self):
        """Stop the entire thread execution."""
        self.mutex.lock()
        self.is_running = False
        self.mutex.unlock()
        self.statusSignal.emit("idle")
        self.wait()

    def run(self):
        """Main execution method for the thread."""
        try:
            if not self.is_running:
                return

            self.mutex.lock()
            self.is_recording = True
            self.mutex.unlock()

            self.statusSignal.emit("recording")
            ConfigManager.console_print("Recording...")
            audio_data = self._record_audio()

            if not self.is_running:
                return

            if audio_data is None:
                self.statusSignal.emit("idle")
                return

            self.statusSignal.emit("transcribing")
            ConfigManager.console_print("Transcribing...")

            # Time the transcription process
            start_time = time.time()
            result = transcribe(audio_data, self.local_model)
            end_time = time.time()

            transcription_time = end_time - start_time
            ConfigManager.console_print(
                f"Transcription completed in {transcription_time:.2f} seconds. "
                f"Post-processed line: {result}"
            )

            if not self.is_running:
                return

            self.statusSignal.emit("idle")
            self.resultSignal.emit(result)

        except Exception:
            traceback.print_exc()
            self.statusSignal.emit("error")
            self.resultSignal.emit("")
        finally:
            self.stop_recording()

    def _resample(self, audio: np.ndarray, from_rate: int, to_rate: int) -> np.ndarray:
        """Resample audio from from_rate to to_rate using linear interpolation."""
        if from_rate == to_rate:
            return audio
        target_len = int(len(audio) * to_rate / from_rate)
        resampled = np.interp(
            np.linspace(0, len(audio) - 1, target_len),
            np.arange(len(audio)),
            audio.astype(np.float32),
        ).astype(np.int16)
        return resampled

    def _query_device_rate(self, device) -> int:
        """Return the native sample rate for the given device index (or system default)."""
        try:
            info = (
                sd.query_devices(device, "input")
                if device is not None
                else sd.query_devices(kind="input")
            )
            return int(info["default_samplerate"])
        except Exception:
            return 16000

    def _open_input_stream(self, device, rate: int, frame_size: int, callback):
        """
        Try to open an InputStream for *device* at *rate*.
        If that fails, warn and fall back to the system default device.
        Returns (stream, actual_device, actual_rate).
        """
        try:
            stream = sd.InputStream(
                samplerate=rate,
                channels=1,
                dtype="int16",
                blocksize=frame_size,
                device=device,
                callback=callback,
            )
            stream.start()
            return stream, device, rate
        except sd.PortAudioError as exc:
            ConfigManager.console_print(
                f"Failed to open device {device} ({exc}). Falling back to system default."
            )
            fallback_rate = self._query_device_rate(None)
            stream = sd.InputStream(
                samplerate=fallback_rate,
                channels=1,
                dtype="int16",
                blocksize=int(fallback_rate * 0.030),
                device=None,
                callback=callback,
            )
            stream.start()
            return stream, None, fallback_rate

    def _record_audio(self):
        """
        Record audio from the microphone.

        :return: numpy array of audio data at self.sample_rate, or None if too short
        """
        recording_options = ConfigManager.get_config_section("recording_options")
        self.sample_rate = recording_options.get("sample_rate") or 16000

        raw_device = recording_options.get("sound_device")
        try:
            sound_device = int(raw_device) if raw_device not in (None, "", "null") else None
        except (ValueError, TypeError):
            sound_device = None

        record_rate = self._query_device_rate(sound_device)

        # webrtcvad only supports these rates
        _VAD_RATES = (8000, 16000, 32000, 48000)
        vad_rate = record_rate if record_rate in _VAD_RATES else 16000

        frame_duration_ms = 30  # ms — required by webrtcvad
        frame_size = int(record_rate * (frame_duration_ms / 1000.0))
        silence_duration_ms = recording_options.get("silence_duration") or 900
        silence_frames = int(silence_duration_ms / frame_duration_ms)

        # 150ms delay before VAD to avoid mistaking key-press sound for voice
        initial_frames_to_skip = int(0.15 * record_rate / frame_size)

        recording_mode = recording_options.get("recording_mode") or "continuous"
        vad = None
        if recording_mode in ("voice_activity_detection", "continuous"):
            vad = webrtcvad.Vad(2)
            speech_detected = False
            silent_frame_count = 0

        audio_buffer = deque(maxlen=frame_size)
        recording = []
        data_ready = Event()

        def audio_callback(indata, frames, time, status):
            if status:
                ConfigManager.console_print(f"Audio callback status: {status}")
            audio_buffer.extend(indata[:, 0])
            data_ready.set()

        stream, sound_device, record_rate = self._open_input_stream(
            sound_device, record_rate, frame_size, audio_callback
        )

        # Recalculate frame_size in case we fell back to a different rate/device
        frame_size = int(record_rate * (frame_duration_ms / 1000.0))
        vad_rate = record_rate if record_rate in _VAD_RATES else 16000

        try:
            while self.is_running and self.is_recording:
                data_ready.wait()
                data_ready.clear()

                if len(audio_buffer) < frame_size:
                    continue

                frame = np.array(list(audio_buffer), dtype=np.int16)
                audio_buffer.clear()
                recording.extend(frame)

                if initial_frames_to_skip > 0:
                    initial_frames_to_skip -= 1
                    continue

                if vad:
                    vad_frame = (
                        self._resample(frame, record_rate, vad_rate)
                        if record_rate != vad_rate
                        else frame
                    )
                    if vad.is_speech(vad_frame.tobytes(), vad_rate):
                        silent_frame_count = 0
                        if not speech_detected:
                            ConfigManager.console_print("Speech detected.")
                            speech_detected = True
                    else:
                        silent_frame_count += 1

                    if speech_detected and silent_frame_count > silence_frames:
                        break
        finally:
            stream.stop()
            stream.close()

        audio_data = np.array(recording, dtype=np.int16)

        if record_rate != self.sample_rate:
            audio_data = self._resample(audio_data, record_rate, self.sample_rate)

        duration = len(audio_data) / self.sample_rate
        ConfigManager.console_print(
            f"Recording finished. Size: {audio_data.size} samples, Duration: {duration:.2f} seconds"
        )

        min_duration_ms = recording_options.get("min_duration") or 100
        if (duration * 1000) < min_duration_ms:
            ConfigManager.console_print("Discarded due to being too short.")
            return None

        return audio_data
