import subprocess
import time
import os

# --- Configuration ---
DEFAULT_OUTPUT_FILENAME = "recorded_audio_ffmpeg.mp3"
DEFAULT_DURATION_HOURS = 24
DEFAULT_DURATION_MINUTES = 0
DEFAULT_DURATION_SECONDS = 0

# --- IMPORTANT: FFmpeg Audio Source Configuration ---
# This is system-dependent for capturing desktop/website audio.
#
# Common options:
# 1. PulseAudio/PipeWire (common in modern Ubuntu Linux):
#    - Try 'default' first.
#    - Look for a 'monitor' source from 'pactl list sources'. 
#      For example, if your speakers are 'alsa_output.pci-0000_03_00.6.analog-stereo',
#      the monitor source might be 'alsa_output.pci-0000_03_00.6.analog-stereo.monitor'.
#
# 2. ALSA (if not using PulseAudio/PipeWire directly or if they are on top of ALSA):
#    - Try 'hw:0,0' or similar. Use 'arecord -L' to list ALSA devices.
#
# To list available audio sources in Ubuntu:
# - For PulseAudio: pactl list sources short
# - For ALSA: arecord -L

# START WITH THIS and then experiment if it doesn't work:
AUDIO_SOURCE_FORMAT = "pulse" # "pulse" for PulseAudio/PipeWire, "alsa" for ALSA
AUDIO_SOURCE_DEVICE = "alsa_output.pci-0000_03_00.6.analog-stereo.monitor" # Device name, e.g., "default", "hw:0,0", or a monitor source name

def get_user_input():
    """
    Prompts user for recording parameters.
    
    Returns:
        tuple: (output_filename, total_duration_seconds)
    """
    print("Audio Recording Configuration")
    print("-" * 30)
    
    # Get filename
    default_name = DEFAULT_OUTPUT_FILENAME
    filename_input = input(f"Output filename [{default_name}]: ").strip()
    filename = filename_input if filename_input else default_name
    # Ensure .mp3 extension
    if not filename.lower().endswith('.mp3'):
        filename += '.mp3'
    
    # Get duration
    try:
        hours = input(f"Recording duration - hours [{DEFAULT_DURATION_HOURS}]: ").strip()
        hours = int(hours) if hours else DEFAULT_DURATION_HOURS
        
        minutes = input(f"Recording duration - minutes [{DEFAULT_DURATION_MINUTES}]: ").strip()
        minutes = int(minutes) if minutes else DEFAULT_DURATION_MINUTES
        
        seconds = input(f"Recording duration - seconds [{DEFAULT_DURATION_SECONDS}]: ").strip()
        seconds = int(seconds) if seconds else DEFAULT_DURATION_SECONDS
        
        total_seconds = (hours * 3600) + (minutes * 60) + seconds
        
        if total_seconds <= 0:
            print("Warning: Invalid duration. Using default of 24 hours.")
            total_seconds = 24 * 3600
    except ValueError:
        print("Warning: Invalid input. Using default duration of 24 hours.")
        total_seconds = 24 * 3600
    
    print("\nConfig Summary:")
    print(f"- Output file: {filename}")
    print(f"- Recording duration: {hours}h {minutes}m {seconds}s ({total_seconds} seconds)")
    print(f"- Audio source: {AUDIO_SOURCE_FORMAT}:{AUDIO_SOURCE_DEVICE}")
    
    # Confirm settings
    confirm = input("\nProceed with these settings? [Y/n]: ").strip().lower()
    if confirm and confirm[0] != 'y':
        print("Recording cancelled.")
        exit(0)
    
    return filename, total_seconds

def check_ffmpeg_installed():
    """Checks if ffmpeg is installed and accessible."""
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("ffmpeg is installed.")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: ffmpeg does not appear to be installed or is not in your PATH.")
        print("Please install ffmpeg. For Ubuntu: sudo apt update && sudo apt install ffmpeg")
        return False

def record_audio_ffmpeg(output_filename: str, duration_seconds: int, audio_format: str, audio_device: str):
    """
    Records audio using ffmpeg for a specified duration from a given audio source.
    """
    if not check_ffmpeg_installed():
        return

    print(f"Starting ffmpeg recording for {duration_seconds} seconds...")
    print(f"Output file: {output_filename}")
    print(f"Using audio format: {audio_format} and device: {audio_device}")
    
    # Calculate expected end time
    end_time = time.time() + duration_seconds
    end_time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))
    print(f"Recording will complete at approximately: {end_time_str}")
    print("If this fails, you likely need to adjust AUDIO_SOURCE_FORMAT and AUDIO_SOURCE_DEVICE in the script.")
    
    # Construct the ffmpeg command
    # -y: Overwrite output file if it exists
    # -f: Input format (e.g., alsa, pulse)
    # -i: Input device/source
    # -t: Duration of recording
    # -acodec: Audio codec (libmp3lame for MP3)
    # -b:a: Audio bitrate for MP3 quality
    # -nostdin: Don't expect any input from stdin (useful for background operation)
    # -nostats: Don't show stats during encoding
    # -loglevel warning: Only show warnings and errors
    command = [
        "ffmpeg",
        "-y",
        "-f", audio_format,
        "-i", audio_device,
        "-t", str(duration_seconds),
        "-acodec", "libmp3lame",  # MP3 codec
        "-b:a", "192k",           # Audio bitrate for MP3 quality
        "-nostdin",               # Don't expect stdin input
        "-nostats",               # Don't show stats during encoding
        "-loglevel", "warning",   # Only show warnings and errors
        output_filename
    ]

    try:
        print(f"Executing command: {' '.join(command)}")
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print("Recording in progress... The audio is being captured silently.")
        print("Press Ctrl+C to stop recording early (output file will contain what was recorded so far).")
        
        try:
            # Wait for the process to complete. ffmpeg will handle the duration via -t.
            stdout, stderr = process.communicate() 

            if process.returncode == 0:
                print("ffmpeg recording finished successfully.")
                if os.path.exists(output_filename) and os.path.getsize(output_filename) > 0:
                    print(f"Audio saved to {output_filename}")
                else:
                    print(f"ffmpeg reported success, but the output file {output_filename} is missing or empty.")
                    print("This can happen if the audio source is silent or not capturing correctly.")
                    print("ffmpeg stderr:", stderr.decode(errors='ignore'))
            else:
                print(f"Error during ffmpeg recording. Return code: {process.returncode}")
                print("ffmpeg stderr:", stderr.decode(errors='ignore'))
                print("Please check the audio source and ffmpeg installation.")
        except KeyboardInterrupt:
            print("\nRecording stopped early by user.")
            process.terminate()
            try:
                process.wait(timeout=5)
                print("ffmpeg process terminated cleanly.")
            except subprocess.TimeoutExpired:
                print("ffmpeg process did not terminate cleanly, forcing...")
                process.kill()
            
            if os.path.exists(output_filename) and os.path.getsize(output_filename) > 0:
                print(f"Partial recording saved to {output_filename}")
            else:
                print("No usable output file was created before termination.")

    except FileNotFoundError:
        print("Error: ffmpeg command not found. Ensure ffmpeg is installed and in your PATH.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def detect_pulseaudio_monitor_source():
    """
    Attempts to detect a PulseAudio monitor source for capturing system audio.
    Returns the name of a suitable monitor source, or None if not found.
    """
    try:
        result = subprocess.run(["pactl", "list", "sources"], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE,
                               text=True)
        
        if result.returncode != 0:
            return None
            
        # Look for monitor sources in the output
        lines = result.stdout.split('\n')
        monitor_sources = []
        current_name = None
        
        for line in lines:
            if line.strip().startswith('Name:'):
                current_name = line.split(':', 1)[1].strip()
            elif '.monitor' in line and current_name:
                monitor_sources.append(current_name)
                
        # Prefer sources with 'monitor' in the name
        for source in monitor_sources:
            if 'monitor' in source:
                return source
                
        # If no clear monitor source found, return the first one if available
        return monitor_sources[0] if monitor_sources else None
        
    except (subprocess.SubprocessError, FileNotFoundError):
        return None

def main():
    """
    Main function to orchestrate audio recording using ffmpeg.
    """
    print("Audio Capture Application using ffmpeg")
    print("--------------------------------------")
    print("This application will record audio without playing it through speakers.")
    
    # Try to auto-detect a suitable monitor source for PulseAudio
    monitor_source = detect_pulseaudio_monitor_source()
    if monitor_source:
        print(f"Found potential monitor source: {monitor_source}")
        print("This source might be suitable for capturing system audio.")
        print(f'You can edit this script to use it by setting AUDIO_SOURCE_DEVICE = "{monitor_source}"')
    
    # Get user input for filename and duration
    filename, duration = get_user_input()

    # Record audio using ffmpeg
    record_audio_ffmpeg(filename, duration, AUDIO_SOURCE_FORMAT, AUDIO_SOURCE_DEVICE)

    print("\n--- Troubleshooting --- ")
    print("If recording fails or the file is silent:")
    print("1. Ensure ffmpeg is installed (`sudo apt install ffmpeg`).")
    print(f"2. Verify AUDIO_SOURCE_FORMAT ('{AUDIO_SOURCE_FORMAT}') and AUDIO_SOURCE_DEVICE ('{AUDIO_SOURCE_DEVICE}') are correct for your system.")
    print("   - For PulseAudio/PipeWire (common on Ubuntu desktops):")
    print("     Run `pactl list sources short` in your terminal.")
    print("     Look for a 'monitor' source, e.g., 'alsa_output.pci-0000_00_1f.3.analog-stereo.monitor'.")
    print("     Set AUDIO_SOURCE_FORMAT = \"pulse\" and AUDIO_SOURCE_DEVICE = <your_monitor_source_name>.")
    print("   - For ALSA directly (less common if Pulse/PipeWire is active):")
    print("     Run `arecord -L` to list devices.")
    print("     Set AUDIO_SOURCE_FORMAT = \"alsa\" and AUDIO_SOURCE_DEVICE = <your_alsa_device_name> (e.g., 'hw:0,0', 'plughw:0,0').")
    print("3. Test ffmpeg directly in the terminal with the command shown in the script output to isolate issues.")

if __name__ == "__main__":
    main()
