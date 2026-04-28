import argparse
import sys
import os
from pathlib import Path
from audio_editor import (
    AudioEditor,
    AudioMerger,
    WaveformVisualizer,
    AudioPlayer,
    create_test_tone,
    generate_waveform_image
)
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def format_duration_str(duration_seconds: float) -> str:
    minutes = int(duration_seconds // 60)
    seconds = duration_seconds % 60
    return f"{minutes:02d}:{seconds:06.3f}"


def cmd_load(args):
    editor = AudioEditor(args.input)
    info = editor.get_audio_info()
    
    print(f"\n{'='*50}")
    print(f"Audio File Information")
    print(f"{'='*50}")
    print(f"File: {args.input}")
    print(f"Duration: {format_duration_str(info['duration_seconds'])}")
    print(f"Sample Rate: {info['sample_rate']} Hz")
    print(f"Samples: {info['samples']:,}")
    print(f"Max Amplitude: {info['max_amplitude']:.4f}")
    print(f"RMS Amplitude: {info['rms']:.4f}")
    print(f"Volume: {info['dBFS']:.2f} dBFS")
    print(f"{'='*50}\n")
    
    if args.visualize:
        editor.visualizer.plot_waveform()
    
    return 0


def cmd_cut(args):
    editor = AudioEditor(args.input)
    info = editor.get_audio_info()
    
    if args.start is None or args.end is None:
        print("Interactive selection mode - use mouse to select region")
        
        def on_select(start, end):
            print(f"Selected: {format_duration_str(start)} to {format_duration_str(end)}")
            print(f"Duration: {format_duration_str(end - start)}")
            if args.save:
                cut_data, sr = editor.cut_audio(start, end)
                output_path = args.output or args.input.replace('.mp3', '_cut.wav')
                if args.output:
                    sf.write(args.output, cut_data, sr)
                else:
                    sf.write(args.input.replace('.mp3', '_cut.wav'), cut_data, sr)
                print(f"Saved to: {output_path}")
        
        import soundfile as sf
        editor.visualizer.plot_with_selection(on_select_callback=on_select)
    else:
        start_seconds = editor._parse_time_string(args.start)
        end_seconds = editor._parse_time_string(args.end)
        
        cut_data, sr = editor.cut_audio(start_seconds, end_seconds)
        
        output_path = args.output or args.input.replace('.mp3', '_cut.wav')
        import soundfile as sf
        sf.write(output_path, cut_data, sr)
        
        print(f"Cut audio from {args.start} to {args.end}")
        print(f"Output: {output_path}")
        print(f"Duration: {format_duration_str(cut_data.shape[0]/sr)}")
    
    return 0


def cmd_merge(args):
    merger = AudioMerger()
    
    input_files = args.input if isinstance(args.input, list) else [args.input]
    
    for file_path in input_files:
        if not os.path.exists(file_path):
            print(f"Error: File not found: {file_path}")
            return 1
        merger.add_file(file_path)
    
    output_path = args.output or 'merged_output.wav'
    import soundfile as sf
    merger.save(output_path, format=args.format)
    
    print(f"Merged {len(input_files)} files into {output_path}")
    
    if args.visualize:
        import soundfile as sf
        merged_data, sr = merger.merge()
        visualizer = WaveformVisualizer(merged_data, sr, title="Merged Audio")
        visualizer.plot_waveform()
    
    return 0


def cmd_waveform(args):
    generate_waveform_image(args.input, args.output, title=args.title or Path(args.input).name)
    print(f"Waveform saved to: {args.output}")
    return 0


def cmd_info(args):
    editor = AudioEditor(args.input)
    info = editor.get_audio_info()
    
    print(f"\n{'='*50}")
    print(f"Audio File Information")
    print(f"{'='*50}")
    print(f"File: {args.input}")
    print(f"Duration: {format_duration_str(info['duration_seconds'])}")
    print(f"Sample Rate: {info['sample_rate']} Hz")
    print(f"Samples: {info['samples']:,}")
    print(f"Max Amplitude: {info['max_amplitude']:.4f}")
    print(f"RMS Amplitude: {info['rms']:.4f}")
    print(f"Volume: {info['dBFS']:.2f} dBFS")
    print(f"{'='*50}\n")
    
    if args.visualize:
        editor.visualizer.plot_waveform()
    
    return 0


def cmd_export(args):
    editor = AudioEditor(args.input)
    
    supported_formats = ['mp3', 'wav', 'ogg', 'flac']
    
    if args.format and args.format.lower() not in supported_formats:
        print(f"Error: Unsupported format. Supported formats: {', '.join(supported_formats)}")
        return 1
    
    output_path = args.output or args.input.rsplit('.', 1)[0] + f'.{args.format or "wav"}'
    editor.export_audio(output_path, format=args.format)
    
    print(f"Exported to: {output_path}")
    
    return 0


def cmd_effects(args):
    editor = AudioEditor(args.input)
    
    if args.fade_in:
        editor.audio_data, editor.sample_rate = editor.fade_in(args.fade_in)
        print(f"Added fade-in: {args.fade_in}ms")
    
    if args.fade_out:
        editor.audio_data, editor.sample_rate = editor.fade_out(args.fade_out)
        print(f"Added fade-out: {args.fade_out}ms")
    
    if args.volume:
        editor.audio_data, editor.sample_rate = editor.change_volume(args.volume)
        print(f"Changed volume by: {args.volume}dB")
    
    if args.normalize:
        editor.audio_data, editor.sample_rate = editor.normalize_audio(args.normalize)
        print(f"Normalized to: {args.normalize}dBFS")
    
    if args.reverse:
        editor.audio_data, editor.sample_rate = editor.reverse_audio()
        print("Reversed audio")
    
    if editor.audio_data is not None:
        output_path = args.output or args.input.rsplit('.', 1)[0] + '_modified.wav'
        import soundfile as sf
        sf.write(output_path, editor.audio_data, editor.sample_rate)
        print(f"Saved to: {output_path}")
    
    return 0


def cmd_test(args):
    frequency = args.frequency or 440
    duration = args.duration or 5000
    
    audio_data, sample_rate = create_test_tone(frequency, duration, args.sample_rate or 44100)
    
    print(f"Created test tone: {frequency}Hz, {duration}ms")
    
    if args.play:
        player = AudioPlayer(audio_data, sample_rate)
        player.play()
    elif args.output:
        import soundfile as sf
        sf.write(args.output, audio_data, sample_rate)
        print(f"Saved to: {args.output}")
    
    return 0


def create_parser():
    parser = argparse.ArgumentParser(
        prog='audio_editor',
        description='Audio editing application with waveform visualization, cutting, and merging capabilities.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s load input.wav                           - Load and display audio info
  %(prog)s load input.wav -v                    - Load and visualize waveform
  %(prog)s cut input.wav --start 00:10 --end 00:30  - Cut audio segment
  %(prog)s merge file1.wav file2.wav -o output.wav - Merge audio files
  %(prog)s waveform input.wav -o waveform.png    - Generate waveform image
  %(prog)s info input.wav                    - Show audio information
  %(prog)s export input.wav -f mp3              - Export to different format
  %(prog)s effects input.wav --fade-in 1000    - Add fade in effect
  %(prog)s test --frequency 440 --duration 5000 - Generate test tone
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    load_parser = subparsers.add_parser('load', help='Load an audio file')
    load_parser.add_argument('input', help='Input audio file')
    load_parser.add_argument('-v', '--visualize', action='store_true', help='Visualize waveform')
    load_parser.set_defaults(func=cmd_load)
    
    cut_parser = subparsers.add_parser('cut', help='Cut audio segment')
    cut_parser.add_argument('input', help='Input audio file')
    cut_parser.add_argument('--start', help='Start time (e.g., 00:10 or 10.5)')
    cut_parser.add_argument('--end', help='End time (e.g., 00:30 or 30.0)')
    cut_parser.add_argument('-o', '--output', help='Output file')
    cut_parser.add_argument('-s', '--save', action='store_true', help='Save after interactive selection')
    cut_parser.set_defaults(func=cmd_cut)
    
    merge_parser = subparsers.add_parser('merge', help='Merge audio files')
    merge_parser.add_argument('input', nargs='+', help='Input audio files')
    merge_parser.add_argument('-o', '--output', help='Output file')
    merge_parser.add_argument('-f', '--format', default='wav', help='Output format')
    merge_parser.add_argument('-v', '--visualize', action='store_true', help='Visualize result')
    merge_parser.set_defaults(func=cmd_merge)
    
    waveform_parser = subparsers.add_parser('waveform', help='Generate waveform image')
    waveform_parser.add_argument('input', help='Input audio file')
    waveform_parser.add_argument('-o', '--output', required=True, help='Output image file')
    waveform_parser.add_argument('-t', '--title', help='Title for waveform')
    waveform_parser.set_defaults(func=cmd_waveform)
    
    info_parser = subparsers.add_parser('info', help='Show audio information')
    info_parser.add_argument('input', help='Input audio file')
    info_parser.add_argument('-v', '--visualize', action='store_true', help='Visualize waveform')
    info_parser.set_defaults(func=cmd_info)
    
    export_parser = subparsers.add_parser('export', help='Export audio to different format')
    export_parser.add_argument('input', help='Input audio file')
    export_parser.add_argument('-o', '--output', help='Output file')
    export_parser.add_argument('-f', '--format', default='wav', help='Output format (mp3, wav, ogg, flac)')
    export_parser.set_defaults(func=cmd_export)
    
    effects_parser = subparsers.add_parser('effects', help='Apply audio effects')
    effects_parser.add_argument('input', help='Input audio file')
    effects_parser.add_argument('--fade-in', type=int, help='Fade in duration in ms')
    effects_parser.add_argument('--fade-out', type=int, help='Fade out duration in ms')
    effects_parser.add_argument('--volume', type=float, help='Volume change in dB')
    effects_parser.add_argument('--normalize', type=float, help='Normalize to target dBFS')
    effects_parser.add_argument('--reverse', action='store_true', help='Reverse audio')
    effects_parser.add_argument('-o', '--output', help='Output file')
    effects_parser.add_argument('-f', '--format', help='Output format')
    effects_parser.set_defaults(func=cmd_effects)
    
    test_parser = subparsers.add_parser('test', help='Generate test tone')
    test_parser.add_argument('-f', '--frequency', type=float, default=440, help='Frequency in Hz')
    test_parser.add_argument('-d', '--duration', type=int, default=5000, help='Duration in ms')
    test_parser.add_argument('-r', '--sample-rate', type=int, default=44100, help='Sample rate')
    test_parser.add_argument('-o', '--output', help='Output file')
    test_parser.add_argument('-p', '--play', action='store_true', help='Play the tone')
    test_parser.set_defaults(func=cmd_test)
    
    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        return args.func(args)
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())