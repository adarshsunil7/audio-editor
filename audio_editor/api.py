import os
import uuid
import logging
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import soundfile as sf
import numpy as np
import librosa
from pathlib import Path
import tempfile
from pydub import AudioSegment

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

SUPPORTED_FORMATS = ['wav', 'mp3', 'flac']
DEFAULT_FORMAT = 'mp3'

def convert_audio(input_path, output_format):
    """Convert audio to specified format."""
    if output_format not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported format: {output_format}")
    
    base, _ = os.path.splitext(input_path)
    output_path = f"{base}.{output_format}"
    
    if output_format == 'mp3':
        audio = AudioSegment.from_wav(input_path)
        audio.export(output_path, format='mp3', bitrate='192k')
    elif output_format == 'flac':
        audio = AudioSegment.from_wav(input_path)
        audio.export(output_path, format='flac')
    else:
        return input_path
    
    return output_path


@app.route('/api/audio/info', methods=['POST'])
def audio_info():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        filename = f"{uuid.uuid4()}_{file.filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            audio_data, sample_rate = sf.read(filepath, dtype='float32')
            if audio_data.ndim > 1:
                audio_data = audio_data.mean(axis=1)
            
            duration = len(audio_data) / sample_rate
            rms = np.sqrt(np.mean(audio_data ** 2))
            dbfs = 20 * np.log10(rms) if rms > 0 else -np.inf
            
            info = {
                'duration': duration,
                'sample_rate': sample_rate,
                'samples': len(audio_data),
                'channels': 1,
                'rms': float(rms),
                'dBFS': float(dbfs),
                'max_amplitude': float(np.max(np.abs(audio_data))),
                'filename': file.filename,
                'id': filename
            }
            
            os.remove(filepath)
            
            return jsonify(info)
            
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            raise e
    
    except Exception as e:
        logger.error(f"Error getting audio info: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/audio/waveform', methods=['POST'])
def audio_waveform():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        filename = f"{uuid.uuid4()}_{file.filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            audio_data, sample_rate = sf.read(filepath, dtype='float32')
            if audio_data.ndim > 1:
                audio_data = audio_data.mean(axis=1)
            
            duration = len(audio_data) / sample_rate
            
            num_points = min(2000, len(audio_data))
            indices = np.linspace(0, len(audio_data) - 1, num_points, dtype=int)
            samples = audio_data[indices]
            
            max_val = np.max(np.abs(samples))
            if max_val > 0:
                samples = (samples / max_val).tolist()
            else:
                samples = samples.tolist()
            
            time_axis = (indices / sample_rate).tolist()
            
            os.remove(filepath)
            
            return jsonify({
                'waveform': samples,
                'time': time_axis,
                'duration': duration,
                'sample_rate': sample_rate
            })
            
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            raise e
    
    except Exception as e:
        logger.error(f"Error generating waveform: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/audio/cut', methods=['POST'])
def audio_cut():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        start_time = float(request.form.get('start', 0))
        end_time = float(request.form.get('end', 0))
        output_format = request.form.get('format', DEFAULT_FORMAT).lower()
        
        filename = f"{uuid.uuid4()}_{file.filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            audio_data, sample_rate = sf.read(filepath, dtype='float32')
            if audio_data.ndim > 1:
                audio_data = audio_data.mean(axis=1)
            
            start_samples = int(max(0, start_time) * sample_rate)
            end_samples = int(min(len(audio_data) / sample_rate, end_time) * sample_rate)
            
            if start_samples >= end_samples:
                return jsonify({'error': 'Invalid time range'}), 400
            
            cut_data = audio_data[start_samples:end_samples]
            
            base_name, _ = os.path.splitext(filename)
            output_filename = f"cut_{base_name}.{output_format}"
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            
            if output_format != 'wav':
                temp_wav = output_path.replace(f'.{output_format}', '.wav')
                sf.write(temp_wav, cut_data, sample_rate)
                output_path = convert_audio(temp_wav, output_format)
                output_filename = os.path.basename(output_path)
                os.remove(temp_wav)
            else:
                sf.write(output_path, cut_data, sample_rate)
            
            os.remove(filepath)
            
            return jsonify({
                'output_file': output_filename,
                'duration': len(cut_data) / sample_rate,
                'start': start_time,
                'end': end_time
            })
            
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            raise e
    
    except Exception as e:
        logger.error(f"Error cutting audio: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/audio/merge', methods=['POST'])
def audio_merge():
    try:
        files = request.files.getlist('files')
        if not files or len(files) < 1:
            return jsonify({'error': 'No files provided'}), 400
        
        saved_files = []
        try:
            segments = []
            sample_rates = []
            
            for file in files:
                if file.filename == '':
                    continue
                
                filename = f"{uuid.uuid4()}_{file.filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                saved_files.append(filepath)
                
                audio_data, sample_rate = sf.read(filepath, dtype='float32')
                if audio_data.ndim > 1:
                    audio_data = audio_data.mean(axis=1)
                
                segments.append(audio_data)
                sample_rates.append(sample_rate)
            
            if not segments:
                return jsonify({'error': 'No valid audio files'}), 400
            
            target_sr = sample_rates[0]
            resampled = []
            for seg, sr in zip(segments, sample_rates):
                if sr != target_sr:
                    seg = librosa.resample(seg, orig_sr=sr, target_sr=target_sr)
                resampled.append(seg)
            
            merged = np.concatenate(resampled)
            
            output_format = request.form.get('format', DEFAULT_FORMAT).lower()
            output_filename = f"merged_{uuid.uuid4()}.{output_format}"
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            
            if output_format != 'wav':
                temp_wav = output_path.replace(f'.{output_format}', '.wav')
                sf.write(temp_wav, merged, target_sr)
                output_path = convert_audio(temp_wav, output_format)
                output_filename = os.path.basename(output_path)
                os.remove(temp_wav)
            else:
                sf.write(output_path, merged, target_sr)
            
            for fp in saved_files:
                os.remove(fp)
            
            return jsonify({
                'output_file': output_filename,
                'duration': len(merged) / target_sr,
                'segments': len(segments)
            })
            
        except Exception as e:
            for fp in saved_files:
                if os.path.exists(fp):
                    os.remove(fp)
            raise e
    
    except Exception as e:
        logger.error(f"Error merging audio: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/audio/effects', methods=['POST'])
def audio_effects():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        fade_in = request.form.get('fade_in', type=int, default=0)
        fade_out = request.form.get('fade_out', type=int, default=0)
        volume = request.form.get('volume', type=float, default=0)
        normalize = request.form.get('normalize', type=float, default=None)
        reverse = request.form.get('reverse', type=bool, default=False)
        output_format = request.form.get('format', DEFAULT_FORMAT).lower()
        
        filename = f"{uuid.uuid4()}_{file.filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            audio_data, sample_rate = sf.read(filepath, dtype='float32')
            if audio_data.ndim > 1:
                audio_data = audio_data.mean(axis=1)
            
            if fade_in > 0:
                num_samples = int(fade_in / 1000.0 * sample_rate)
                num_samples = min(num_samples, len(audio_data))
                fade_curve = np.linspace(0, 1, num_samples)
                audio_data[:num_samples] *= fade_curve
            
            if fade_out > 0:
                num_samples = int(fade_out / 1000.0 * sample_rate)
                num_samples = min(num_samples, len(audio_data))
                fade_curve = np.linspace(1, 0, num_samples)
                audio_data[-num_samples:] *= fade_curve
            
            if volume != 0:
                factor = 10 ** (volume / 20)
                audio_data *= factor
                max_val = np.max(np.abs(audio_data))
                if max_val > 1.0:
                    audio_data = audio_data / max_val
            
            if normalize is not None:
                rms = np.sqrt(np.mean(audio_data ** 2))
                current_dbfs = 20 * np.log10(rms) if rms > 0 else -np.inf
                db_change = normalize - current_dbfs
                factor = 10 ** (db_change / 20)
                audio_data *= factor
                max_val = np.max(np.abs(audio_data))
                if max_val > 1.0:
                    audio_data = audio_data / max_val
            
            if reverse:
                audio_data = audio_data[::-1]
            
            base_name, _ = os.path.splitext(filename)
            output_filename = f"effect_{base_name}.{output_format}"
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            
            if output_format != 'wav':
                temp_wav = output_path.replace(f'.{output_format}', '.wav')
                sf.write(temp_wav, audio_data, sample_rate)
                output_path = convert_audio(temp_wav, output_format)
                output_filename = os.path.basename(output_path)
                os.remove(temp_wav)
            else:
                sf.write(output_path, audio_data, sample_rate)
            
            os.remove(filepath)
            
            effects_applied = []
            if fade_in > 0:
                effects_applied.append('fade_in')
            if fade_out > 0:
                effects_applied.append('fade_out')
            if volume != 0:
                effects_applied.append(f'volume_{volume}dB')
            if normalize is not None:
                effects_applied.append(f'normalize_{normalize}dBFS')
            if reverse:
                effects_applied.append('reverse')
            
            return jsonify({
                'output_file': output_filename,
                'duration': len(audio_data) / sample_rate,
                'effects': effects_applied
            })
            
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            raise e
    
    except Exception as e:
        logger.error(f"Error applying effects: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/audio/download/<path:filename>', methods=['GET'])
def download_file(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(filepath, as_attachment=True)


@app.route('/api/audio/test', methods=['GET'])
def create_test_tone():
    try:
        frequency = request.args.get('frequency', type=float, default=440)
        duration = request.args.get('duration', type=int, default=3000)
        sample_rate = request.args.get('sample_rate', type=int, default=44100)
        output_format = request.args.get('format', DEFAULT_FORMAT).lower()
        
        num_samples = int(duration / 1000.0 * sample_rate)
        t = np.linspace(0, duration / 1000.0, num_samples, dtype='float32')
        tone = np.sin(2 * np.pi * frequency * t).astype('float32')
        
        output_filename = f"test_tone_{uuid.uuid4()}.{output_format}"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        
        if output_format != 'wav':
            temp_wav = output_path.replace(f'.{output_format}', '.wav')
            sf.write(temp_wav, tone, sample_rate)
            output_path = convert_audio(temp_wav, output_format)
            output_filename = os.path.basename(output_path)
            os.remove(temp_wav)
        else:
            sf.write(output_path, tone, sample_rate)
        
        return jsonify({
            'output_file': output_filename,
            'frequency': frequency,
            'duration': duration / 1000.0,
            'sample_rate': sample_rate
        })
    
    except Exception as e:
        logger.error(f"Error creating test tone: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)