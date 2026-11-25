# Audio capture

How the app turns your voice into audio it can transcribe. Source: `src/result_thread.py` (`_record_audio`) and
`src/audio/`.

> This app records **from the microphone only**. It does not open audio files, export audio, or process
> multiple speakers.

## Pipeline

1. **Open the microphone** (`audio/stream.py`) using the device in `recording_options.sound_device` (empty = the Windows
   default) at that device's native sample rate. If the chosen device cannot be opened, it falls back to the system default
   and says so in the log.
2. **Read 30 ms frames.** The audio callback fills a buffer; the recording loop takes one 30 ms frame at a time and appends
   it to the recording. Samples are 16-bit integers, mono (first channel).
3. **Ignore the first 150 ms** for speech detection, so the click of the hotkey is not mistaken for speech.
4. **Detect speech and silence** (modes `continuous` and `voice_activity_detection` only) with
   [WebRTC VAD](https://github.com/wiseman/py-webrtcvad) at aggressiveness 2. The VAD needs 8/16/32/48 kHz; other rates
   are resampled for the detector only.
5. **Stop** when the mode says so: after speech has been heard and then `silence_duration` ms (default 900) of silence
   (`continuous`, `voice_activity_detection`); when the hotkey is pressed again (`press_to_toggle`); when the hotkey is
   released (`hold_to_record`); or when the app/session is stopped.
6. **Resample** the whole recording to `recording_options.sample_rate` (default 16000 Hz, what Whisper expects) with
   linear interpolation (`audio/resampler.py`).
7. **Discard** recordings shorter than `min_duration` ms (default 100) as accidental key presses.
8. Hand the audio to [transcription](real-time-transcription.md).

## Settings

| Setting (`recording_options.`) | Default | Effect |
|---|---|---|
| `sound_device` | *(system default)* | Which microphone. |
| `sample_rate` | `16000` | Rate of the audio passed to Whisper. Leave at 16000 unless you know why. |
| `silence_duration` | `900` ms | How long a pause ends an utterance. Raise it if sentences are cut in two at your natural pauses; lower it for snappier response. |
| `min_duration` | `100` ms | Shortest recording that is processed. |
| `recording_mode` | `continuous` | When recording ends (see the [README](../README.md#use-it)). |

Full list: [configuration reference](configuration.md).
