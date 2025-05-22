import subprocess
import time
import os

# --- Configuration ---
# For a 24-hour recording, ensure you have sufficient disk space.
# A 24-hour MP3 file (stereo, 192kbps) will be much smaller than WAV (approx. 2 GB).
DEFAULT_OUTPUT_FILENAME = "recorded_audio_ffmpeg_24h.mp3"
DEFAULT_DURATION_SECONDS = 10 * 60 * 60  # 24 hours in seconds

# --- IMPORTANT: FFmpeg Audio Source Configuration ---
# This is HIGHLY system-dependent, especially on WSL.
# You will likely need to change this value.
#
# Common options:
# 1. PulseAudio/PipeWire (often the default in modern Linux/WSL setups):
#    - Try 'default' first.
#    - Look for a 'monitor' source from 'pactl list sources'. 
#      For example, if your speakers are 'alsa_output.pci-0000_00_1f.3.analog-stereo',
#      the monitor source might be 'alsa_output.pci-0000_00_1f.3.analog-stereo.monitor'.
#    audio_source = "default" 
#    audio_source = "alsa_output.pci-0000_00_1f.3.analog-stereo.monitor" # Example, replace with your actual monitor source
#
# 2. ALSA (if not using PulseAudio/PipeWire directly or if they are on top of ALSA):
#    - Try 'hw:0,0' or similar. Use 'arecord -L' to list ALSA devices.
#    audio_source = "hw:0,0" 
# 
# For WSL, you are trying to capture the audio output that Windows is playing.
# This usually means you need "Stereo Mix" or "What U Hear" enabled on the Windows host
# and then select the corresponding source that PipeWire/PulseAudio exposes to WSL from that.
# It might appear as 'default' if WSL audio is correctly routing the Windows loopback,
# or it might have a more specific name.

# START WITH THIS and then experiment if it doesn't work:
AUDIO_SOURCE_FORMAT = "pulse" # "pulse" for PulseAudio/PipeWire, "alsa" for ALSA
AUDIO_SOURCE_DEVICE = "default" # Device name, e.g., "default", "hw:0,0", or a monitor source name

# You can also try to list devices using ffmpeg, though it's less straightforward for input devices:
# On Linux, for ALSA: ffmpeg -f alsa -list_devices true -i dummy
# For PulseAudio, it usually relies on system tools like `pactl list sources`

def check_ffmpeg_installed():
    """Checks if ffmpeg is installed and accessible."""
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("ffmpeg is installed.")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: ffmpeg does not appear to be installed or is not in your PATH.")
        print("Please install ffmpeg. For Debian/Ubuntu: sudo apt update && sudo apt install ffmpeg")
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
    print("If this fails, you likely need to adjust AUDIO_SOURCE_FORMAT and AUDIO_SOURCE_DEVICE in the script.")

    # Construct the ffmpeg command
    # -y: Overwrite output file if it exists
    # -f: Input format (e.g., alsa, pulse, dshow for windows directshow)
    # -i: Input device/source
    # -t: Duration of recording
    # -acodec: Audio codec (libmp3lame for MP3)
    # -b:a: Audio bitrate for MP3 quality
    command = [
        "ffmpeg",
        "-y",
        "-f", audio_format,
        "-i", audio_device,
        "-t", str(duration_seconds),
        "-acodec", "libmp3lame",  # MP3 codec
        "-b:a", "192k",           # Audio bitrate for MP3 quality
        output_filename
    ]

    try:
        print(f"Executing command: {' '.join(command)}")
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for the process to complete. ffmpeg will handle the duration via -t.
        # Removing timeout for long recordings, Python will wait until ffmpeg exits.
        stdout, stderr = process.communicate() 

        if process.returncode == 0:
            print("ffmpeg recording finished successfully.")
            if os.path.exists(output_filename) and os.path.getsize(output_filename) > 0:
                print(f"Audio saved to {output_filename}")
            else:
                print(f"ffmpeg reported success, but the output file {output_filename} is missing or empty.")
                print("This can happen if the audio source is silent or not capturing correctly.")
                print("ffmpeg stdout:", stdout.decode(errors='ignore'))
                print("ffmpeg stderr:", stderr.decode(errors='ignore'))
        else:
            print(f"Error during ffmpeg recording. Return code: {process.returncode}")
            print("ffmpeg stdout:", stdout.decode(errors='ignore'))
            print("ffmpeg stderr:", stderr.decode(errors='ignore'))
            print("Please check the audio source and ffmpeg installation.")

    except subprocess.TimeoutExpired: # This block might be less likely to be hit now
        print("ffmpeg process timed out. Killing the process.")
        process.kill()
        stdout, stderr = process.communicate()
        print("ffmpeg stdout (on timeout):", stdout.decode(errors='ignore'))
        print("ffmpeg stderr (on timeout):", stderr.decode(errors='ignore'))
    except FileNotFoundError:
        print("Error: ffmpeg command not found. Ensure ffmpeg is installed and in your PATH.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def main():
    """
    Main function to orchestrate audio recording using ffmpeg.
    """
    print("Audio Capture Application using ffmpeg")
    print("--------------------------------------")

    # --- Customizable Parameters ---
    filename = DEFAULT_OUTPUT_FILENAME
    duration = DEFAULT_DURATION_SECONDS

    # Record audio using ffmpeg
    record_audio_ffmpeg(filename, duration, AUDIO_SOURCE_FORMAT, AUDIO_SOURCE_DEVICE)

    # print("\n--- Troubleshooting --- ")
    # print("If recording fails or the file is silent:")
    # print("1. Ensure ffmpeg is installed (`sudo apt install ffmpeg`).")
    # print(f"2. Verify AUDIO_SOURCE_FORMAT ('{AUDIO_SOURCE_FORMAT}') and AUDIO_SOURCE_DEVICE ('{AUDIO_SOURCE_DEVICE}') are correct for your system.")
    # print("   - For PulseAudio/PipeWire (common on WSL/Linux desktops):")
    # print("     Run `pactl list sources short` in your WSL terminal.")
    # print("     Look for a 'monitor' source, e.g., 'alsa_output.pci-0000_00_1f.3.analog-stereo.monitor'.")
    # print("     Set AUDIO_SOURCE_FORMAT = \"pulse\" and AUDIO_SOURCE_DEVICE = <your_monitor_source_name>.")
    # print("   - For ALSA directly (less common if Pulse/PipeWire is active):")
    # print("     Run `arecord -L` to list devices.")
    # print("     Set AUDIO_SOURCE_FORMAT = \"alsa\" and AUDIO_SOURCE_DEVICE = <your_alsa_device_name> (e.g., 'hw:0,0', 'plughw:0,0').")
    # print("3. Ensure 'Stereo Mix' or equivalent is enabled in Windows sound settings (Recording tab) if capturing desktop audio.")
    # print("4. Test ffmpeg directly in the terminal with the command shown in the script output to isolate issues.")

if __name__ == "__main__":
    main()
