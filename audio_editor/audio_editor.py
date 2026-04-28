import numpy as np
import soundfile as sf
import librosa
import matplotlib.pyplot as plt
from matplotlib.widgets import SpanSelector, Button
from matplotlib.ticker import FuncFormatter
import matplotlib
from scipy.io import wavfile
import os
from pathlib import Path
from typing import Optional, List, Tuple, Union
import logging
import threading
import queue

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WaveformVisualizer:
    def __init__(self, audio_data: np.ndarray, sample_rate: int, title: str = "Audio Waveform"):
        self.audio_data = audio_data
        self.sample_rate = sample_rate
        self.title = title
        self.fig = None
        self.ax = None
        self.line = None
        self.selection = None
        self.start_time = None
        self.end_time = None
        self.on_select_callback = None
        self.duration = len(audio_data) / sample_rate
        
    @classmethod
    def from_file(cls, file_path: str, title: Optional[str] = None):
        audio_data, sample_rate = sf.read(file_path, dtype='float32')
        if audio_data.ndim > 1:
            audio_data = audio_data.mean(axis=1)
        title = title or Path(file_path).name
        return cls(audio_data, sample_rate, title)
    
    def _format_time(self, x, pos):
        minutes = int(x // 60)
        seconds = int(x % 60)
        ms = int((x - int(x)) * 1000)
        return f"{minutes:02d}:{seconds:02d}.{ms:03d}"
    
    def plot_waveform(self, show: bool = True, downsample: int = 10) -> matplotlib.figure.Figure:
        if downsample > 1:
            samples = self.audio_data[::downsample]
            time_axis = np.linspace(0, self.duration, len(samples))
        else:
            samples = self.audio_data
            time_axis = np.linspace(0, self.duration, len(samples))
        
        self.fig, self.ax = plt.subplots(figsize=(14, 6))
        self.fig.canvas.manager.set_window_title(self.title)
        
        max_val = np.max(np.abs(samples))
        if max_val > 0:
            samples_normalized = samples / max_val
        else:
            samples_normalized = samples
        
        self.line, = self.ax.plot(time_axis, samples_normalized, color='#2196F3', linewidth=0.5, alpha=0.8)
        
        self.ax.set_xlabel('Time', fontsize=12)
        self.ax.set_ylabel('Amplitude', fontsize=12)
        self.ax.set_title(self.title, fontsize=14, fontweight='bold')
        self.ax.set_xlim(0, self.duration)
        self.ax.set_ylim(-1.1, 1.1)
        self.ax.axhline(y=0, color='black', linewidth=0.3, alpha=0.5)
        self.ax.grid(True, alpha=0.3)
        self.ax.xaxis.set_major_formatter(FuncFormatter(self._format_time))
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        if show:
            plt.show()
        
        return self.fig
    
    def plot_with_selection(self, on_select_callback=None) -> Tuple[matplotlib.figure.Figure, SpanSelector]:
        self.on_select_callback = on_select_callback
        
        return self.plot_waveform(show=True)
    
    def _on_select(self, xmin: float, xmax: float):
        self.start_time = xmin
        self.end_time = xmax
        logger.info(f"Selected region: {self._format_time(xmin, None)} to {self._format_time(xmax, None)}")
        
        if self.on_select_callback:
            self.on_select_callback(xmin, xmax)
    
    def plot_multi_track(self, audio_tracks: List[Tuple[np.ndarray, int]], show: bool = True, downsample: int = 10) -> matplotlib.figure.Figure:
        num_tracks = len(audio_tracks)
        max_duration = max((len(audio) / sr for audio, sr in audio_tracks), default=0)
        
        self.fig, axes = plt.subplots(num_tracks, 1, figsize=(14, 4 * num_tracks), sharex=True)
        
        if num_tracks == 1:
            axes = [axes]
        
        colors = ['#2196F3', '#4CAF50', '#FF9800', '#E91E63', '#9C27B0']
        
        for idx, (ax, (audio, sample_rate)) in enumerate(zip(axes, audio_tracks)):
            if downsample > 1:
                audio = audio[::downsample]
            
            duration = len(audio) / sample_rate
            
            max_val = np.max(np.abs(audio))
            if max_val > 0:
                audio = audio / max_val
            
            time_axis = np.linspace(0, duration, len(audio))
            
            ax.plot(time_axis, audio, color=colors[idx % len(colors)], linewidth=0.5, alpha=0.8, label=f"Track {idx + 1}")
            ax.set_ylabel('Amplitude', fontsize=10)
            ax.set_ylim(-1.1, 1.1)
            ax.axhline(y=0, color='black', linewidth=0.3, alpha=0.5)
            ax.grid(True, alpha=0.3)
            ax.legend(loc='upper right')
        
        axes[-1].set_xlabel('Time', fontsize=12)
        axes[-1].xaxis.set_major_formatter(FuncFormatter(self._format_time))
        
        self.fig.suptitle(self.title, fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        if show:
            plt.show()
        
        return self.fig
    
    def save_plot(self, filename: str, dpi: int = 150):
        if self.fig is None:
            self.plot_waveform(show=False)
        
        self.fig.savefig(filename, dpi=dpi, bbox_inches='tight', facecolor='white')
        logger.info(f"Waveform saved to {filename}")


class AudioEditor:
    SUPPORTED_FORMATS = ['.wav', '.mp3', '.ogg', '.flac', '.aiff', '.aif', '.m4a']
    
    def __init__(self, file_path: Optional[str] = None):
        self.audio_data: Optional[np.ndarray] = None
        self.sample_rate: int = 44100
        self.original_file_path: Optional[str] = None
        self.visualizer: Optional[WaveformVisualizer] = None
        
        if file_path:
            self.load_audio(file_path)
    
    def load_audio(self, file_path: str) -> Tuple[np.ndarray, int]:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        
        extension = file_path.suffix.lower()
        if extension not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported audio format: {extension}")
        
        try:
            self.audio_data, self.sample_rate = sf.read(str(file_path), dtype='float32')
            
            if self.audio_data.ndim > 1:
                self.audio_data = self.audio_data.mean(axis=1)
            
            self.original_file_path = str(file_path)
            self.visualizer = WaveformVisualizer(
                self.audio_data, 
                self.sample_rate,
                title=f"Waveform - {file_path.name}"
            )
            
            logger.info(f"Loaded audio: {file_path.name} ({self.duration:.2f}s, {self.sample_rate}Hz)")
            
            return self.audio_data, self.sample_rate
            
        except Exception as e:
            raise ValueError(f"Failed to load audio file: {e}")
    
    @property
    def duration(self) -> float:
        if self.audio_data is None:
            return 0.0
        return len(self.audio_data) / self.sample_rate
    
    def get_audio_info(self) -> dict:
        if self.audio_data is None:
            return {}
        
        rms = np.sqrt(np.mean(self.audio_data ** 2))
        dbfs = 20 * np.log10(rms) if rms > 0 else -np.inf
        
        return {
            'duration_seconds': self.duration,
            'channels': 1 if self.audio_data.ndim == 1 else self.audio_data.shape[1],
            'sample_rate': self.sample_rate,
            'samples': len(self.audio_data),
            'rms': rms,
            'dBFS': dbfs,
            'max_amplitude': np.max(np.abs(self.audio_data)),
            'format': Path(self.original_file_path).suffix if self.original_file_path else None
        }
    
    def cut_audio(self, start_seconds: float, end_seconds: float) -> Tuple[np.ndarray, int]:
        if self.audio_data is None:
            raise ValueError("No audio loaded")
        
        start_samples = int(max(0, start_seconds) * self.sample_rate)
        end_samples = int(min(self.duration, end_seconds) * self.sample_rate)
        
        if start_samples >= end_samples:
            raise ValueError("Start time must be less than end time")
        
        cut_data = self.audio_data[start_samples:end_samples]
        
        logger.info(f"Cut audio from {start_seconds}s to {end_seconds}s ({len(cut_data)/self.sample_rate:.2f}s)")
        
        return cut_data, self.sample_rate
    
    def cut_by_time(self, start_time: str, end_time: str) -> Tuple[np.ndarray, int]:
        start_seconds = self._parse_time_string(start_time)
        end_seconds = self._parse_time_string(end_time)
        return self.cut_audio(start_seconds, end_seconds)
    
    def _parse_time_string(self, time_str: str) -> float:
        time_str = time_str.strip()
        
        if ':' in time_str:
            parts = time_str.split(':')
            if len(parts) == 2:
                minutes = int(parts[0])
                seconds = float(parts[1])
                return minutes * 60 + seconds
            elif len(parts) == 3:
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = float(parts[2])
                return hours * 3600 + minutes * 60 + seconds
        
        return float(time_str)
    
    def merge_audio(self, audio_segments: List[np.ndarray], sample_rates: List[int]) -> Tuple[np.ndarray, int]:
        if not audio_segments:
            raise ValueError("No audio segments provided")
        
        merged = np.concatenate(audio_segments)
        
        if sample_rates:
            target_sr = sample_rates[0]
            if not all(sr == target_sr for sr in sample_rates):
                resampled = []
                for seg, sr in zip(audio_segments, sample_rates):
                    if sr != target_sr:
                        seg = librosa.resample(seg, orig_sr=sr, target_sr=target_sr)
                    resampled.append(seg)
                merged = np.concatenate(resampled)
                target_sr = target_sr
            else:
                target_sr = sample_rates[0]
        else:
            target_sr = self.sample_rate
        
        logger.info(f"Merged {len(audio_segments)} segments (total: {len(merged)/target_sr:.2f}s)")
        
        return merged, target_sr
    
    def concatenate_files(self, file_paths: List[str], crossfade_ms: int = 0) -> Tuple[np.ndarray, int]:
        segments = []
        sample_rates = []
        
        for file_path in file_paths:
            data, sr = sf.read(file_path, dtype='float32')
            if data.ndim > 1:
                data = data.mean(axis=1)
            segments.append(data)
            sample_rates.append(sr)
        
        return self.merge_audio(segments, sample_rates)
    
    def export_audio(self, output_path: str, format: Optional[str] = None) -> str:
        if self.audio_data is None:
            raise ValueError("No audio to export")
        
        output_path = Path(output_path)
        
        if format is None:
            format = output_path.suffix[1:].lower() if output_path.suffix else 'wav'
        
        if format == 'mp3':
            import tempfile
            import subprocess
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                tmp_path = tmp.name
            sf.write(tmp_path, self.audio_data, self.sample_rate)
            subprocess.run(['ffmpeg', '-i', tmp_path, '-y', '-acodec', 'libmp3lame', output_path])
            os.unlink(tmp_path)
        else:
            sf.write(str(output_path), self.audio_data, self.sample_rate)
        
        logger.info(f"Exported audio to {output_path}")
        
        return str(output_path)
    
    def create_silence(self, duration_ms: int, sample_rate: Optional[int] = None) -> Tuple[np.ndarray, int]:
        if sample_rate is None:
            sample_rate = self.sample_rate
        num_samples = int(duration_ms / 1000.0 * sample_rate)
        silence = np.zeros(num_samples, dtype='float32')
        logger.info(f"Created silence: {duration_ms}ms")
        return silence, sample_rate
    
    def fade_in(self, duration_ms: int) -> Tuple[np.ndarray, int]:
        if self.audio_data is None:
            raise ValueError("No audio loaded")
        
        num_samples = int(duration_ms / 1000.0 * self.sample_rate)
        num_samples = min(num_samples, len(self.audio_data))
        
        fade_curve = np.linspace(0, 1, num_samples)
        faded = self.audio_data.copy()
        faded[:num_samples] *= fade_curve
        
        logger.info(f"Added fade-in: {duration_ms}ms")
        
        return faded, self.sample_rate
    
    def fade_out(self, duration_ms: int) -> Tuple[np.ndarray, int]:
        if self.audio_data is None:
            raise ValueError("No audio loaded")
        
        num_samples = int(duration_ms / 1000.0 * self.sample_rate)
        num_samples = min(num_samples, len(self.audio_data))
        
        fade_curve = np.linspace(1, 0, num_samples)
        faded = self.audio_data.copy()
        faded[-num_samples:] *= fade_curve
        
        logger.info(f"Added fade-out: {duration_ms}ms")
        
        return faded, self.sample_rate
    
    def change_volume(self, db_change: float) -> Tuple[np.ndarray, int]:
        if self.audio_data is None:
            raise ValueError("No audio loaded")
        
        factor = 10 ** (db_change / 20)
        changed = self.audio_data * factor
        
        max_val = np.max(np.abs(changed))
        if max_val > 1.0:
            changed = changed / max_val
        
        logger.info(f"Changed volume by {db_change}dB")
        
        return changed, self.sample_rate
    
    def reverse_audio(self) -> Tuple[np.ndarray, int]:
        if self.audio_data is None:
            raise ValueError("No audio loaded")
        
        reversed_audio = self.audio_data[::-1]
        
        logger.info("Reversed audio")
        
        return reversed_audio, self.sample_rate
    
    def normalize_audio(self, target_dbfs: float = -3.0) -> Tuple[np.ndarray, int]:
        if self.audio_data is None:
            raise ValueError("No audio loaded")
        
        rms = np.sqrt(np.mean(self.audio_data ** 2))
        current_dbfs = 20 * np.log10(rms) if rms > 0 else -np.inf
        
        db_change = target_dbfs - current_dbfs
        factor = 10 ** (db_change / 20)
        normalized = self.audio_data * factor
        
        max_val = np.max(np.abs(normalized))
        if max_val > 1.0:
            normalized = normalized / max_val
        
        logger.info(f"Normalized audio to {target_dbfs}dBFS")
        
        return normalized, self.sample_rate
    
    def adjust_speed(self, speed_factor: float) -> Tuple[np.ndarray, int]:
        if self.audio_data is None:
            raise ValueError("No audio loaded")
        
        if speed_factor <= 0:
            raise ValueError("Speed factor must be positive")
        
        new_length = int(len(self.audio_data) / speed_factor)
        adjusted = librosa.resample(self.audio_data, orig_sr=self.sample_rate, target_sr=int(self.sample_rate * speed_factor))
        
        logger.info(f"Adjusted speed by {speed_factor}x")
        
        return adjusted[:new_length], self.sample_rate
    
    def pitch_shift(self, semitones: float) -> Tuple[np.ndarray, int]:
        if self.audio_data is None:
            raise ValueError("No audio loaded")
        
        shifted = librosa.effects.pitch_shift(self.audio_data, sr=self.sample_rate, n_steps=semitones)
        
        logger.info(f"Pitch shifted by {semitones} semitones")
        
        return shifted, self.sample_rate


class AudioMerger:
    def __init__(self):
        self.segments: List[Tuple[np.ndarray, int, Optional[str]]] = []
        self.output_file: Optional[str] = None
    
    def add_segment(self, audio_data: np.ndarray, sample_rate: int, label: Optional[str] = None):
        self.segments.append((audio_data, sample_rate, label))
        duration = len(audio_data) / sample_rate
        logger.info(f"Added segment: {label or 'Untitled'} ({duration:.2f}s)")
    
    def add_file(self, file_path: str, label: Optional[str] = None):
        data, sr = sf.read(file_path, dtype='float32')
        if data.ndim > 1:
            data = data.mean(axis=1)
        self.add_segment(data, sr, label or Path(file_path).name)
    
    def add_editor(self, editor: AudioEditor, label: Optional[str] = None):
        if editor.audio_data is None:
            raise ValueError("Editor has no audio loaded")
        self.add_segment(editor.audio_data, editor.sample_rate, label)
    
    def merge(self) -> Tuple[np.ndarray, int]:
        if not self.segments:
            raise ValueError("No segments to merge")
        
        audio_data = [seg[0] for seg in self.segments]
        sample_rates = [seg[1] for seg in self.segments]
        target_sr = sample_rates[0]
        
        if not all(sr == target_sr for sr in sample_rates):
            resampled = []
            for seg, sr in zip(audio_data, sample_rates):
                if sr != target_sr:
                    seg = librosa.resample(seg, orig_sr=sr, target_sr=target_sr)
                resampled.append(seg)
            audio_data = resampled
        
        merged = np.concatenate(audio_data)
        
        logger.info(f"Merged {len(audio_data)} segments (total: {len(merged)/target_sr:.2f}s)")
        
        return merged, target_sr
    
    def save(self, output_path: str, format: Optional[str] = None):
        merged, sample_rate = self.merge()
        
        output_path = Path(output_path)
        if format is None:
            format = output_path.suffix[1:].lower() if output_path.suffix else 'wav'
        
        if format == 'mp3':
            import tempfile
            import subprocess
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                tmp_path = tmp.name
            sf.write(tmp_path, merged, sample_rate)
            subprocess.run(['ffmpeg', '-i', tmp_path, '-y', '-acodec', 'libmp3lame', output_path])
            os.unlink(tmp_path)
        else:
            sf.write(str(output_path), merged, sample_rate)
        
        logger.info(f"Saved merged audio to {output_path}")
        
        self.output_file = str(output_path)
        
        return self.output_file
    
    def clear(self):
        self.segments.clear()
        logger.info("Cleared all segments")


class AudioPlayer:
    def __init__(self, audio_data: Optional[np.ndarray] = None, sample_rate: int = 44100):
        self.audio_data = audio_data
        self.sample_rate = sample_rate
        self._playing = False
    
    def load(self, file_path: str):
        self.audio_data, self.sample_rate = sf.read(file_path, dtype='float32')
        if self.audio_data.ndim > 1:
            self.audio_data = self.audio_data.mean(axis=1)
        logger.info(f"Loaded audio for playback: {file_path}")
    
    def play(self):
        if self.audio_data is None:
            raise ValueError("No audio loaded")
        
        try:
            import sounddevice as sd
            self._playing = True
            sd.play(self.audio_data, self.sample_rate)
            sd.wait()
            self._playing = False
        except ImportError:
            logger.warning("sounddevice not installed, using simple playback")
            import simpleaudio as sa
            audio_int16 = (self.audio_data * 32767).astype(np.int16)
            play_obj = sa.PlayBuffer(audio_int16, self.sample_rate)
            play_obj.start()
            play_obj.wait_done()
    
    def stop(self):
        try:
            import sounddevice as sd
            sd.stop()
        except ImportError:
            pass
    
    def play_async(self):
        if self.audio_data is None:
            raise ValueError("No audio loaded")
        
        def _play():
            try:
                import sounddevice as sd
                sd.play(self.audio_data, self.sample_rate)
                sd.wait()
            except ImportError:
                import simpleaudio as sa
                audio_int16 = (self.audio_data * 32767).astype(np.int16)
                play_obj = sa.PlayBuffer(audio_int16, self.sample_rate)
                play_obj.start()
                play_obj.wait_done()
        
        thread = threading.Thread(target=_play)
        thread.start()
    
    def preview_segment(self, start_seconds: float, duration_seconds: float = 5.0):
        if self.audio_data is None:
            raise ValueError("No audio loaded")
        
        start_samples = int(start_seconds * self.sample_rate)
        end_samples = int(min(start_seconds + duration_seconds, self.duration) * self.sample_rate)
        segment = self.audio_data[start_samples:end_samples]
        
        player = AudioPlayer(segment, self.sample_rate)
        player.play()
    
    @property
    def duration(self) -> float:
        if self.audio_data is None:
            return 0.0
        return len(self.audio_data) / self.sample_rate


def create_test_tone(frequency: float = 440, duration_ms: int = 5000, sample_rate: int = 44100) -> Tuple[np.ndarray, int]:
    num_samples = int(duration_ms / 1000.0 * sample_rate)
    t = np.linspace(0, duration_ms / 1000.0, num_samples, dtype='float32')
    tone = np.sin(2 * np.pi * frequency * t).astype('float32')
    logger.info(f"Created test tone: {frequency}Hz for {duration_ms}ms at {sample_rate}Hz")
    return tone, sample_rate


def generate_waveform_image(audio_file: str, output_file: str, title: Optional[str] = None):
    visualizer = WaveformVisualizer.from_file(audio_file, title)
    visualizer.save_plot(output_file)
    return output_file