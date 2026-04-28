import React, { useState, useRef, useEffect, useCallback } from 'react';
import styled from 'styled-components';
import { api } from './api';

const Container = styled.div`
  min-height: 100vh;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  padding: 2rem;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
`;

const Header = styled.header`
  text-align: center;
  margin-bottom: 2rem;
`;

const Title = styled.h1`
  color: #00d9ff;
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
  text-shadow: 0 0 20px rgba(0, 217, 255, 0.3);
`;

const Subtitle = styled.p`
  color: #8b8b9e;
  font-size: 1rem;
`;

const MainCard = styled.div`
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
  border: 1px solid rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
`;

const Button = styled.button`
  background: ${props => props.$primary ? 'linear-gradient(135deg, #00d9ff 0%, #00a8cc 100%)' : 'rgba(255, 255, 255, 0.1)'};
  color: ${props => props.$primary ? '#1a1a2e' : '#fff'};
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  margin: 0.5rem;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 20px rgba(0, 217, 255, 0.3);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }
`;

const IconButton = styled(Button)`
  padding: 12px 16px;
  font-size: 1.2rem;
`;

const ButtonGroup = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 1rem;
`;

const FileInput = styled.input`
  display: none;
`;

const FormatSelect = styled.select`
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  border: 1px solid rgba(0, 217, 255, 0.3);
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 0.9rem;
  cursor: pointer;
  outline: none;

  &:hover {
    border-color: #00d9ff;
  }

  option {
    background: #1a1a2e;
    color: #fff;
  }
`;

const FormatLabel = styled.label`
  color: #8b8b9e;
  font-size: 0.85rem;
  margin-right: 8px;
`;

const FileLabel = styled.label`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  border: 2px dashed rgba(0, 217, 255, 0.3);
  border-radius: 12px;
  background: rgba(0, 217, 255, 0.05);
  cursor: pointer;
  transition: all 0.3s ease;
  color: #8b8b9e;

  &:hover {
    border-color: #00d9ff;
    background: rgba(0, 217, 255, 0.1);
  }
`;

const UploadIcon = styled.div`
  font-size: 3rem;
  margin-bottom: 1rem;
`;

const AudioInfo = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  margin: 1.5rem 0;
`;

const InfoCard = styled.div`
  background: rgba(255, 255, 255, 0.05);
  padding: 1rem;
  border-radius: 8px;
  text-align: center;
`;

const InfoLabel = styled.div`
  color: #8b8b9e;
  font-size: 0.85rem;
  margin-bottom: 0.25rem;
`;

const InfoValue = styled.div`
  color: #00d9ff;
  font-size: 1.25rem;
  font-weight: 600;
`;

const ErrorMessage = styled.div`
  background: rgba(255, 82, 82, 0.1);
  border: 1px solid rgba(255, 82, 82, 0.3);
  color: #ff5252;
  padding: 1rem;
  border-radius: 8px;
  margin: 1rem 0;
`;

const SuccessMessage = styled.div`
  background: rgba(0, 255, 136, 0.1);
  border: 1px solid rgba(0, 255, 136, 0.3);
  color: #00ff88;
  padding: 1rem;
  border-radius: 8px;
  margin: 1rem 0;
`;

const WaveformContainer = styled.div`
  position: relative;
  margin: 2rem 0;
  user-select: none;
`;

const WaveformCanvas = styled.canvas`
  width: 100%;
  height: 200px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  cursor: crosshair;
  display: block;
`;

const TimeDisplay = styled.div`
  position: absolute;
  bottom: 10px;
  ${props => props.$position === 'start' ? 'left: 10px;' : 'right: 10px;'}
  color: #8b8b9e;
  font-size: 0.85rem;
  background: rgba(0, 0, 0, 0.6);
  padding: 4px 8px;
  border-radius: 4px;
`;

const PlayerControls = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  margin: 1.5rem 0;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
`;

const ProgressBar = styled.input`
  flex: 1;
  height: 6px;
  -webkit-appearance: none;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
  outline: none;

  &::-webkit-slider-thumb {
    -webkit-appearance: none;
    width: 16px;
    height: 16px;
    background: #00d9ff;
    border-radius: 50%;
    cursor: pointer;
  }
`;

const SelectionInfo = styled.div`
  display: flex;
  justify-content: center;
  gap: 2rem;
  margin: 1rem 0;
  padding: 1rem;
  background: rgba(0, 217, 255, 0.1);
  border-radius: 8px;
  border: 1px solid rgba(0, 217, 255, 0.3);
`;

function formatDuration(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  const ms = Math.floor((seconds % 1) * 1000);
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}.${ms.toString().padStart(3, '0')}`;
}

function formatTime(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = (seconds % 60).toFixed(2);
  return `${mins.toString().padStart(2, '0')}:${secs.padStart(5, '0')}`;
}

export default function App() {
  const [file, setFile] = useState(null);
  const [audioInfo, setAudioInfo] = useState(null);
  const [waveform, setWaveform] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [outputFormat, setOutputFormat] = useState('mp3');
  
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [selection, setSelection] = useState({ start: 0, end: 0 });
  const [isSelecting, setIsSelecting] = useState(false);
  const [selectionStart, setSelectionStart] = useState(null);
  const [audioUrl, setAudioUrl] = useState(null);
  
  const audioRef = useRef(null);
  const canvasRef = useRef(null);
  const containerRef = useRef(null);
  const animationRef = useRef(null);
  
  const handleFileSelect = async (e) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;
    
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
    }
    
    const newAudioUrl = URL.createObjectURL(selectedFile);
    setAudioUrl(newAudioUrl);
    setFile(selectedFile);
    setLoading(true);
    setError(null);
    setSuccess(null);
    setSelection({ start: 0, end: 0 });
    setCurrentTime(0);
    setIsPlaying(false);
    
    try {
      const info = await api.getAudioInfo(selectedFile);
      setAudioInfo(info);
      setSelection({ start: 0, end: info.duration });
      
      const waveformData = await api.getWaveform(selectedFile);
      setWaveform(waveformData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handlePlayPause = async () => {
    if (!audioRef.current) return;
    
    try {
      if (isPlaying) {
        audioRef.current.pause();
        setIsPlaying(false);
      } else {
        if (selection.start > 0 || selection.end < audioInfo.duration) {
          audioRef.current.currentTime = selection.start;
        }
        await audioRef.current.play();
        setIsPlaying(true);
      }
    } catch (err) {
      console.error('Play error:', err);
      setIsPlaying(false);
    }
  };

  const handleTimeUpdate = () => {
    if (!audioRef.current) return;
    setCurrentTime(audioRef.current.currentTime);
    
    if (selection.end > 0 && audioRef.current.currentTime >= selection.end) {
      audioRef.current.pause();
      setIsPlaying(false);
    }
  };

  const handleSeek = (e) => {
    if (!audioRef.current) return;
    const time = parseFloat(e.target.value);
    audioRef.current.currentTime = time;
    setCurrentTime(time);
  };

  const handleMouseDown = (e) => {
    if (!waveform || !containerRef.current) return;
    
    const rect = containerRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const clickTime = (x / rect.width) * waveform.duration;
    
    setSelectionStart(Math.max(0, Math.min(clickTime, waveform.duration)));
    setIsSelecting(true);
  };

  const handleMouseMove = (e) => {
    if (!isSelecting || !selectionStart || !waveform || !containerRef.current) return;
    
    const rect = containerRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const currentPos = (x / rect.width) * waveform.duration;
    const clampedPos = Math.max(0, Math.min(currentPos, waveform.duration));
    
    const start = Math.min(selectionStart, clampedPos);
    const end = Math.max(selectionStart, clampedPos);
    
    setSelection({ start, end });
  };

  const handleMouseUp = () => {
    setIsSelecting(false);
    setSelectionStart(null);
  };

  const drawWaveform = useCallback(() => {
    if (!waveform || !waveform.waveform || !canvasRef.current) return;
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    
    ctx.clearRect(0, 0, width, height);
    
    const data = waveform.waveform;
    const barWidth = width / data.length;
    
    ctx.fillStyle = 'rgba(0, 217, 255, 0.15)';
    const selStartX = (selection.start / waveform.duration) * width;
    const selEndX = (selection.end / waveform.duration) * width;
    ctx.fillRect(selStartX, 0, selEndX - selStartX, height);
    
    const playX = (currentTime / waveform.duration) * width;
    ctx.strokeStyle = '#00ff88';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(playX, 0);
    ctx.lineTo(playX, height);
    ctx.stroke();
    
    ctx.fillStyle = '#00d9ff';
    for (let i = 0; i < data.length; i++) {
      const x = i * barWidth;
      const barHeight = Math.abs(data[i]) * height * 0.85;
      const y = (height - barHeight) / 2;
      ctx.fillRect(x, y, barWidth - 0.5, barHeight);
    }
    
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
    ctx.beginPath();
    ctx.moveTo(0, height / 2);
    ctx.lineTo(width, height / 2);
    ctx.stroke();
  }, [waveform, selection, currentTime]);

  useEffect(() => {
    if (waveform) {
      requestAnimationFrame(() => drawWaveform());
    }
  }, [waveform, drawWaveform]);

  useEffect(() => {
    const handleGlobalMouseUp = () => {
      if (isSelecting) {
        setIsSelecting(false);
        setSelectionStart(null);
      }
    };
    
    window.addEventListener('mouseup', handleGlobalMouseUp);
    return () => window.removeEventListener('mouseup', handleGlobalMouseUp);
  }, [isSelecting]);

  const handleCut = async () => {
    if (!file || selection.start >= selection.end) {
      setError('Please select a valid region to cut');
      return;
    }
    
    setLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      const result = await api.cutAudio(file, selection.start, selection.end, outputFormat);
      setSuccess(`Audio cut successfully! Duration: ${formatDuration(result.duration)}`);
      
      const downloadUrl = api.getDownloadUrl(result.output_file);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = `cut_audio.${outputFormat}`;
      link.click();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTestTone = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);
    
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
    }
    
    try {
      const result = await api.createTestTone(440, 3000, 44100, outputFormat);
      setSuccess('Test tone created!');
      
      const downloadUrl = api.getDownloadUrl(result.output_file);
      const response = await fetch(downloadUrl);
      const blob = await response.blob();
      const newAudioUrl = URL.createObjectURL(blob);
      
      if (audioRef.current) {
        audioRef.current.src = newAudioUrl;
      }
      
      setAudioUrl(newAudioUrl);
      setFile(blob);
      setAudioInfo({
        duration: result.duration,
        sample_rate: result.sample_rate,
        filename: `test_tone.${outputFormat}`
      });
      setSelection({ start: 0, end: result.duration });
      
      const waveformData = await api.getWaveform(blob, outputFormat);
      setWaveform(waveformData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleApplyEffects = async (effects) => {
    if (!file) return;
    
    setLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      const result = await api.applyEffects(file, effects, outputFormat);
      setSuccess(`Effects applied: ${result.effects.join(', ')}`);
      
      const downloadUrl = api.getDownloadUrl(result.output_file);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = `effects_audio.${outputFormat}`;
      link.click();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let animationFrame;
    const updatePlayhead = () => {
      if (audioRef.current && isPlaying) {
        setCurrentTime(audioRef.current.currentTime);
        animationFrame = requestAnimationFrame(updatePlayhead);
      }
    };
    
    if (isPlaying) {
      animationFrame = requestAnimationFrame(updatePlayhead);
    }
    
    return () => {
      if (animationFrame) {
        cancelAnimationFrame(animationFrame);
      }
    };
  }, [isPlaying]);

  return (
    <Container>
      <audio
        ref={audioRef}
        src={audioUrl || undefined}
        onTimeUpdate={handleTimeUpdate}
        onEnded={() => setIsPlaying(false)}
        onLoadedMetadata={() => {
          if (audioRef.current) {
            setCurrentTime(0);
          }
        }}
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
      />
      
      <Header>
        <Title>Audio Editor</Title>
        <Subtitle>Edit, cut, merge and visualize audio files</Subtitle>
      </Header>
      
      <MainCard>
        {!file && (
          <div>
            <FileLabel htmlFor="file-input">
              <UploadIcon>🎵</UploadIcon>
              <div>Drop audio file here or click to browse</div>
              <div style={{ fontSize: '0.85rem', marginTop: '0.5rem', color: '#666' }}>
                Supports WAV, MP3, OGG, FLAC
              </div>
            </FileLabel>
            <FileInput
              id="file-input"
              type="file"
              accept="audio/*"
              onChange={handleFileSelect}
            />
            
            <div style={{ textAlign: 'center', marginTop: '2rem' }}>
              <p style={{ color: '#8b8b9e', marginBottom: '1rem' }}>Or create a test tone</p>
              <Button onClick={handleCreateTestTone} disabled={loading}>
                Generate Test Tone
              </Button>
            </div>
          </div>
        )}
        
        {file && audioInfo && (
          <div>
            <AudioInfo>
              <InfoCard>
                <InfoLabel>Filename</InfoLabel>
                <InfoValue>{audioInfo.filename}</InfoValue>
              </InfoCard>
              <InfoCard>
                <InfoLabel>Duration</InfoLabel>
                <InfoValue>{formatDuration(audioInfo.duration)}</InfoValue>
              </InfoCard>
              <InfoCard>
                <InfoLabel>Sample Rate</InfoLabel>
                <InfoValue>{audioInfo.sample_rate} Hz</InfoValue>
              </InfoCard>
              <InfoCard>
                <InfoLabel>Volume</InfoLabel>
                <InfoValue>{audioInfo.dBFS?.toFixed(1) || 'N/A'} dBFS</InfoValue>
              </InfoCard>
            </AudioInfo>
            
            <PlayerControls>
              <IconButton onClick={handlePlayPause} disabled={loading}>
                {isPlaying ? '⏸️' : '▶️'}
              </IconButton>
              
              <span style={{ color: '#8b8b9e', minWidth: '60px' }}>
                {formatTime(currentTime)}
              </span>
              
              <ProgressBar
                type="range"
                min={0}
                max={audioInfo.duration}
                step={0.01}
                value={currentTime}
                onChange={handleSeek}
              />
              
              <span style={{ color: '#8b8b9e', minWidth: '60px' }}>
                {formatTime(audioInfo.duration)}
              </span>
            </PlayerControls>
            
            <SelectionInfo>
              <div>
                <InfoLabel>Selection Start</InfoLabel>
                <InfoValue>{formatTime(selection.start)}</InfoValue>
              </div>
              <div>
                <InfoLabel>Selection End</InfoLabel>
                <InfoValue>{formatTime(selection.end)}</InfoValue>
              </div>
              <div>
                <InfoLabel>Selection Duration</InfoLabel>
                <InfoValue>{formatDuration(selection.end - selection.start)}</InfoValue>
              </div>
            </SelectionInfo>
            
            <WaveformContainer
              ref={containerRef}
              onMouseDown={handleMouseDown}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
            >
              <WaveformCanvas
                ref={canvasRef}
                width={1100}
                height={200}
              />
              <TimeDisplay $position="start">
                {formatTime(selection.start)}
              </TimeDisplay>
              <TimeDisplay $position="end">
                {formatTime(selection.end)}
              </TimeDisplay>
            </WaveformContainer>
            
            <div style={{ color: '#8b8b9e', textAlign: 'center', fontSize: '0.85rem', marginBottom: '1rem' }}>
              Click and drag on the waveform to select a region
            </div>
            
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1rem' }}>
              <FormatLabel>Output Format:</FormatLabel>
              <FormatSelect value={outputFormat} onChange={(e) => setOutputFormat(e.target.value)}>
                <option value="mp3">MP3</option>
                <option value="wav">WAV</option>
                <option value="flac">FLAC</option>
              </FormatSelect>
            </div>
            
            <ButtonGroup>
              <Button $primary onClick={handleCut} disabled={loading}>
                Cut Selection
              </Button>
              <Button onClick={() => handleApplyEffects({ fade_in: 1000 })} disabled={loading}>
                Fade In
              </Button>
              <Button onClick={() => handleApplyEffects({ fade_out: 1000 })} disabled={loading}>
                Fade Out
              </Button>
              <Button onClick={() => handleApplyEffects({ normalize: -3 })} disabled={loading}>
                Normalize
              </Button>
              <Button onClick={() => handleApplyEffects({ volume: -6 })} disabled={loading}>
                Lower Volume
              </Button>
              <Button onClick={() => handleApplyEffects({ reverse: true })} disabled={loading}>
                Reverse
              </Button>
              <Button onClick={() => {
                if (audioUrl) {
                  URL.revokeObjectURL(audioUrl);
                }
                setFile(null);
                setAudioInfo(null);
                setWaveform(null);
                setSelection({ start: 0, end: 0 });
                setCurrentTime(0);
                setIsPlaying(false);
                setAudioUrl(null);
                if (audioRef.current) {
                  audioRef.current.pause();
                  audioRef.current.src = '';
                }
              }}>
                Clear
              </Button>
            </ButtonGroup>
          </div>
        )}
        
        {error && <ErrorMessage>{error}</ErrorMessage>}
        {success && <SuccessMessage>{success}</SuccessMessage>}
        
        {loading && (
          <div style={{ textAlign: 'center', padding: '2rem', color: '#00d9ff' }}>
            Processing...
          </div>
        )}
      </MainCard>
    </Container>
  );
}