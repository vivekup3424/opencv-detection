import cv2
import time
import datetime
import argparse
import subprocess
import shlex

def detect_motion_record(rtsp_url, threshold=25, min_area=500, skip_frames=10):
    print(f"Connecting to RTSP stream: {rtsp_url}")

    cap = cv2.VideoCapture(rtsp_url)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)
    time.sleep(2)
    if not cap.isOpened():
        print("Error: Could not open RTSP stream")
        return

    print("Connected. Waiting for initial frame...")

    for _ in range(100):
        ret, frame1 = cap.read()
        if ret:
            break
        time.sleep(0.1)
    if not ret:
        print("Error: Could not get initial frame")
        return

    # Prepare first frame downscaled grayscale
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray1 = cv2.resize(gray1, (320, 240))
    gray1 = cv2.GaussianBlur(gray1, (21, 21), 0)

    motion_detected = False
    last_motion_time = None
    recording_process = None

    frame_count = 0

    try:
        while True:
            ret, frame2 = cap.read()
            if not ret:
                print("Stream ended or error reading frame")
                break

            frame_count += 1

            # Always keep original frame for recording, but skip detection frames
            if frame_count % skip_frames == 0:
                # Downscale and prepare for detection
                gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
                gray2 = cv2.resize(gray2, (320, 240))
                gray2 = cv2.GaussianBlur(gray2, (21, 21), 0)

                frame_delta = cv2.absdiff(gray1, gray2)
                thresh = cv2.threshold(frame_delta, threshold, 255, cv2.THRESH_BINARY)[1]
                thresh = cv2.dilate(thresh, None, iterations=2)
                contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                motion_this_frame = False
                for contour in contours:
                    if cv2.contourArea(contour) < min_area:
                        continue
                    motion_this_frame = True
                    break

                if motion_this_frame:
                    if not motion_detected:
                        motion_detected = True
                        last_motion_time = time.time()
                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"recordings/motion_{timestamp}.mp4"
                        print(f"Motion detected. Starting recording: {filename}")

                        # Start ffmpeg recording process
                        ffmpeg_cmd = (
                            f"ffmpeg -y -rtsp_transport tcp -i \"{rtsp_url}\" "
                            f"-c copy -t 00:05:00 {shlex.quote(filename)}"
                        )
                        recording_process = subprocess.Popen(shlex.split(ffmpeg_cmd))
                    else:
                        last_motion_time = time.time()
                else:
                    # If no motion for 5 seconds, stop recording
                    if motion_detected and (time.time() - last_motion_time > 5):
                        print("Motion stopped. Stopping recording.")
                        motion_detected = False
                        if recording_process:
                            recording_process.terminate()
                            recording_process.wait()
                            recording_process = None

                # Update previous frame for next detection
                gray1 = gray2

            # Sleep a bit to avoid tight loop
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("Interrupted by user")

    finally:
        if recording_process:
            recording_process.terminate()
            recording_process.wait()
        cap.release()
        print("Cleanup done.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RTSP Motion Detection + Recording")
    parser.add_argument("--url", type=str, required=True, help="RTSP stream URL")
    parser.add_argument("--threshold", type=int, default=25, help="Motion detection threshold")
    parser.add_argument("--min-area", type=int, default=500, help="Minimum contour area for motion")
    parser.add_argument("--skip-frames", type=int, default=10, help="Process every Nth frame for detection")
    args = parser.parse_args()

    print(f"Starting detection with skip_frames={args.skip_frames}")
    detect_motion_record(args.url, args.threshold, args.min_area, args.skip_frames)