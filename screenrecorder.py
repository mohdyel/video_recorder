import os
import time
import msvcrt
import subprocess
import signal
from moviepy.editor import VideoFileClip, AudioFileClip

def prompt_filename():
    # Step 1: Prompt for the MP4 filename
    filename = input("Enter video filename (with .mp4 extension): ").strip()
    if not filename.endswith('.mp4'):
        filename += '.mp4'
    while os.path.exists(filename):
        choice = input(f"File '{filename}' exists. Replace (r) or new (n)? [r/n]: ").lower()
        if choice == 'r':
            os.remove(filename)
            break
        elif choice == 'n':
            filename = input("Enter a new MP4 filename: ").strip()
            if not filename.endswith('.mp4'):
                filename += '.mp4'
        else:
            print("Invalid choice. Please type 'r' or 'n'.")
    return filename

def wait_for_esc():
    print("Recording started. Press ESC to stop recording gracefully...")
    while True:
        if msvcrt.kbhit():
            key = msvcrt.getch()
            # ESC key returns b'\x1b'
            if key == b'\x1b':
                print("ESC pressed. Stopping recording gracefully...")
                return
        time.sleep(0.1)

def wait_for_file(filename, timeout=30):
    start = time.time()
    while not os.path.exists(filename):
        if time.time() - start > timeout:
            raise TimeoutError(f"Timeout waiting for {filename} to be created.")
        time.sleep(0.5)

def main():
    # Prompt for the final merged MP4 filename
    output_filename = prompt_filename()

    # Start the C# recorder program (program.exe) in a new process group
    print("Starting program.exe...")
    process = subprocess.Popen(
        ["AudioRecorder.exe"],
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
    )

    # Wait for the user to press ESC
    wait_for_esc()

    # Instead of killing the process, send CTRL_BREAK_EVENT to close the task gracefully
    print("Sending CTRL_BREAK_EVENT to program.exe...")
    os.kill(process.pid, signal.CTRL_BREAK_EVENT)

    # Wait for the process to exit naturally
    try:
        process.wait(timeout=10)
        print("program.exe closed gracefully.")
    except subprocess.TimeoutExpired:
        print("program.exe did not exit gracefully within the timeout.")

    # Wait for the recording files to be generated
    try:
        wait_for_file("screen_recording.mp4")
        wait_for_file("recorded_audio.wav")
    except TimeoutError as e:
        print(e)
        return

    # Merge using MoviePy
    print("Merging audio and video using MoviePy...")
    try:
        video_clip = VideoFileClip("screen_recording.mp4")
        audio_clip = AudioFileClip("recorded_audio.wav")
        final_clip = video_clip.set_audio(audio_clip)
        final_clip.write_videofile(output_filename, codec="libx264", audio_codec="aac")
        print("Merging completed successfully.")
    except Exception as e:
        print("Error during merging:", e)
        return

    # Delete intermediate files
    for f in ["screen_recording.mp4", "recorded_audio.wav"]:
        try:
            os.remove(f)
            print(f"Deleted {f}")
        except Exception as e:
            print(f"Could not delete {f}: {e}")

if __name__ == "__main__":
    main()
