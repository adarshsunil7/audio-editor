const API_BASE = 'http://localhost:5001';

export const api = {
  async getAudioInfo(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE}/api/audio/info`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to get audio info');
    }
    
    return response.json();
  },
  
  async getWaveform(file, format = 'wav') {
    const formData = new FormData();
    const fileToUpload = file instanceof Blob 
      ? new File([file], `audio.${format}`, { type: format === 'mp3' ? 'audio/mpeg' : format === 'flac' ? 'audio/flac' : 'audio/wav' })
      : file;
    formData.append('file', fileToUpload);
    
    const response = await fetch(`${API_BASE}/api/audio/waveform`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to generate waveform');
    }
    
    return response.json();
  },
  
  async cutAudio(file, start, end, format = 'mp3') {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('start', start.toString());
    formData.append('end', end.toString());
    formData.append('format', format);
    
    const response = await fetch(`${API_BASE}/api/audio/cut`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to cut audio');
    }
    
    return response.json();
  },
  
  async mergeAudio(files, format = 'mp3') {
    const formData = new FormData();
    files.forEach((file, index) => {
      formData.append('files', file);
    });
    formData.append('format', format);
    
    const response = await fetch(`${API_BASE}/api/audio/merge`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to merge audio');
    }
    
    return response.json();
  },
  
  async applyEffects(file, effects, format = 'mp3') {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('format', format);
    
    Object.entries(effects).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== false) {
        formData.append(key, value.toString());
      }
    });
    
    const response = await fetch(`${API_BASE}/api/audio/effects`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to apply effects');
    }
    
    return response.json();
  },
  
  async createTestTone(frequency = 440, duration = 3000, sampleRate = 44100, format = 'mp3') {
    const params = new URLSearchParams({
      frequency: frequency.toString(),
      duration: duration.toString(),
      sample_rate: sampleRate.toString(),
      format: format,
    });
    
    const response = await fetch(`${API_BASE}/api/audio/test?${params}`);
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to create test tone');
    }
    
    return response.json();
  },
  
  getDownloadUrl(filename) {
    return `${API_BASE}/api/audio/download/${filename}`;
  }
};