import os
import subprocess
import argparse
import sys
import re
import time

def get_video_files():
    extensions = ('.mp4', '.mov', '.mkv', '.avi', '.wmv', '.flv', '.webm')
    return [f for f in os.listdir('.') if f.lower().endswith(extensions) and not f.endswith('_denoised.mp4')]

def get_duration(input_file):
    cmd = [
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1', input_file
    ]
    try:
        output = subprocess.check_output(cmd).decode().strip()
        return float(output)
    except:
        return None

def check_hardware_acceleration():
    cmd = ['ffmpeg', '-encoders']
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode()
        if 'h264_qsv' in output:
            return 'h264_qsv'
        elif 'h264_amf' in output:
            return 'h264_amf'
        return None
    except:
        return None

def denoise_video(input_file, preset, output_file=None, progress_callback=None):
    if not output_file:
        base, _ = os.path.splitext(input_file)
        output_file = f"{base}_denoised.mp4"

    presets = {
        'fast': 'atadenoise=0.05:0.05:0.1',
        'balanced': 'hqdn3d=4.0:3.0:6.0:4.5',
        'hq': 'nlmeans=s=1.5:p=7:r=15'
    }

    filter_str = presets.get(preset, presets['balanced'])
    hw_encoder = check_hardware_acceleration()
    
    cmd = ['ffmpeg', '-i', input_file, '-vf', filter_str]
    
    if hw_encoder:
        cmd.extend(['-c:v', hw_encoder, '-global_quality', '20'])
    else:
        cmd.extend(['-c:v', 'libx264', '-crf', '18', '-preset', 'medium'])

    cmd.extend(['-c:a', 'copy', '-pix_fmt', 'yuv420p', '-y', output_file])

    duration = get_duration(input_file)
    process = subprocess.Popen(cmd, stderr=subprocess.PIPE, universal_newlines=True)
    time_pattern = re.compile(r"time=(\d+:\d+:\d+\.\d+)")

    try:
        while True:
            line = process.stderr.readline()
            if not line and process.poll() is not None:
                break
            
            match = time_pattern.search(line)
            if match and duration and progress_callback:
                time_str = match.group(1)
                h, m, s = map(float, time_str.split(':'))
                current_time = h * 3600 + m * 60 + s
                progress = min((current_time / duration), 1.0)
                progress_callback(progress)

        process.wait()
        return process.returncode == 0, output_file
    except:
        return False, None

def main():
    parser = argparse.ArgumentParser(description="AI Video Denoiser CLI (Optimized)")
    parser.add_argument("-i", "--input", help="Path to input video file")
    parser.add_argument("-p", "--preset", choices=['fast', 'balanced', 'hq'], default='balanced', 
                        help="Denoising strength preset (default: balanced)")
    parser.add_argument("-o", "--output", help="Custom output filename")

    args = parser.parse_args()

    input_file = args.input
    if not input_file:
        videos = get_video_files()
        if not videos:
            print("No video files found.")
            return
        
        if len(videos) == 1:
            input_file = videos[0]
        else:
            for idx, vid in enumerate(videos):
                print(f"{idx + 1}. {vid}")
            choice = int(input("\nSelect a video number: ")) - 1
            input_file = videos[choice]

    denoise_video(input_file, args.preset, args.output)

if __name__ == "__main__":
    main()
