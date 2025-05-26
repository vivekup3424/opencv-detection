import cv2, time, datetime, argparse, collections, psutil, shutil, threading, json
from pathlib import Path
# Constants
DEFAULT_THRESHOLD = 25
DEFAULT_MIN_AREA = 500
SKIP_FRAMES = 10
DEFAULT_PRE_BUFFER_SECONDS = 5
DEFAULT_POST_BUFFER_SECONDS = 5
DEFAULT_FPS = 30
BUFFER_SIZE = 3
MAX_INIT_FRAMES = 100
INIT_FRAME_WAIT = 0.1
MOTION_DETECT_RESOLUTION = (160, 120)
GAUSSIAN_KERNEL = (15, 15)
RECORDINGS_DIR = "recordings"
CLEANUP_DAYS = 3
CHUNK_DURATION_SECONDS = 60  # 1 minute chunks
ADAPTIVE_SLEEP_NO_MOTION = 0.05
ADAPTIVE_SLEEP_MOTION = 0.01

def cleanup_old_recordings(camera_id):
    """Remove recording directories older than CLEANUP_DAYS"""
    camera_dir = Path(RECORDINGS_DIR) / camera_id
    if not camera_dir.exists():
        return
    
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=CLEANUP_DAYS)
    
    for date_dir in camera_dir.iterdir():
        if date_dir.is_dir():
            try:
                # Parse directory name as date (YYYY-MM-DD format)
                dir_date = datetime.datetime.strptime(date_dir.name, '%Y-%m-%d')
                if dir_date < cutoff_date:
                    print(f"Cleaning up old recordings: {date_dir}")
                    shutil.rmtree(date_dir)
            except ValueError:
                # Skip directories that don't match date format
                continue

def detect_motion_record(rtsp_url, camera_id, threshold=DEFAULT_THRESHOLD, min_area=DEFAULT_MIN_AREA, 
                         skip_frames=SKIP_FRAMES, pre_buffer_seconds=DEFAULT_PRE_BUFFER_SECONDS,
                         post_buffer_seconds=DEFAULT_POST_BUFFER_SECONDS, stop_event=None):
    """Motion detection with pre/post buffer recording (t-5 to s+5 seconds)"""
    thread_name = f"[{camera_id}]"
    print(f"{thread_name} Connecting to RTSP stream: {rtsp_url}")
    
    # Setup recording directory and cleanup
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    recording_dir = Path(RECORDINGS_DIR) / camera_id / today
    recording_dir.mkdir(parents=True, exist_ok=True)
    cleanup_old_recordings(camera_id)
    
    # Initialize capture
    cap = cv2.VideoCapture(rtsp_url)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, BUFFER_SIZE)
    time.sleep(2)
    if not cap.isOpened():
        return print(f"{thread_name} Error: Could not open RTSP stream")

    # Get initial frame
    ret = None
    for _ in range(MAX_INIT_FRAMES):
        ret, frame1 = cap.read()
        if ret: break
        time.sleep(INIT_FRAME_WAIT)
    if not ret:
        return print(f"{thread_name} Error: Could not get initial frame")

    fps = cap.get(cv2.CAP_PROP_FPS) or DEFAULT_FPS
    frame_buffer = collections.deque(maxlen=int(fps * pre_buffer_seconds))
    print(f"{thread_name} Buffer: {pre_buffer_seconds}s at {fps} FPS ({frame_buffer.maxlen} frames)")
    
    # Initialize variables
    gray1 = cv2.GaussianBlur(cv2.resize(cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY), MOTION_DETECT_RESOLUTION), GAUSSIAN_KERNEL, 0)
    motion_detected = False
    motion_start_time = last_motion_time = recording_process = temp_video_file = chunk_start_time = None
    chunk_counter = consecutive_no_motion_frames = frame_count = frames_processed_for_detection = 0
    start_time = last_stats_time = time.time()

    try:
        while True:
            if stop_event and stop_event.is_set():
                print(f"{thread_name} Stopping camera thread...")
                break
                
            ret, frame2 = cap.read()
            if not ret: break

            # Buffer management and recording
            if not motion_detected: frame_buffer.append((frame2.copy(), time.time()))
            if motion_detected and temp_video_file: temp_video_file.write(frame2)
            frame_count += 1

            # Motion detection (every skip_frames)
            if frame_count % skip_frames == 0:
                frames_processed_for_detection += 1
                gray2 = cv2.GaussianBlur(cv2.resize(cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY), MOTION_DETECT_RESOLUTION), GAUSSIAN_KERNEL, 0)
                thresh = cv2.dilate(cv2.threshold(cv2.absdiff(gray1, gray2), threshold, 255, cv2.THRESH_BINARY)[1], None, iterations=1)
                contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                motion_this_frame = any(cv2.contourArea(c) >= min_area for c in contours)

                if motion_this_frame:
                    consecutive_no_motion_frames = 0
                    if not motion_detected:
                        motion_detected = True
                        motion_start_time = last_motion_time = chunk_start_time = time.time()
                        chunk_counter = 1
                        timestamp = datetime.datetime.now().strftime('%H%M%S')
                        filename = recording_dir / f"motion_{timestamp}_chunk{chunk_counter:03d}.mp4"
                        print(f"{thread_name} Motion detected. Recording chunk {chunk_counter}: {filename}")
                        
                        height, width, _ = frame_buffer[0][0].shape
                        temp_video_file = cv2.VideoWriter(str(filename), cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))
                        
                        for buffered_frame, _ in frame_buffer:
                            temp_video_file.write(buffered_frame)
                        frame_buffer.clear()
                    else:
                        last_motion_time = time.time()
                        # Check chunk duration
                        if temp_video_file and (time.time() - chunk_start_time >= CHUNK_DURATION_SECONDS):
                            print(f"{thread_name} Chunk {chunk_counter} duration reached. Starting new chunk...")
                            temp_video_file.release()
                            chunk_counter += 1
                            chunk_start_time = time.time()
                            timestamp = datetime.datetime.now().strftime('%H%M%S')
                            filename = recording_dir / f"motion_{timestamp}_chunk{chunk_counter:03d}.mp4"
                            print(f"{thread_name} Recording chunk {chunk_counter}: {filename}")
                            height, width, _ = frame2.shape
                            temp_video_file = cv2.VideoWriter(str(filename), cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))
                else:
                    consecutive_no_motion_frames += 1
                    if motion_detected and (time.time() - last_motion_time > post_buffer_seconds):
                        print(f"{thread_name} Motion stopped. Recording {post_buffer_seconds} more seconds for chunk {chunk_counter}...")
                        
                        # Record post-buffer frames
                        post_buffer_frames = int(fps * post_buffer_seconds)
                        for i in range(post_buffer_frames):
                            ret, post_frame = cap.read()
                            if not ret: break
                            if temp_video_file: temp_video_file.write(post_frame)
                            time.sleep(1.0 / fps)
                            
                            # Check chunk duration during post-buffer
                            if temp_video_file and (time.time() - chunk_start_time >= CHUNK_DURATION_SECONDS) and i < int(fps * post_buffer_seconds) - 1:
                                print(f"{thread_name} Post-buffer chunk {chunk_counter} duration reached. Starting new chunk...")
                                temp_video_file.release()
                                chunk_counter += 1
                                chunk_start_time = time.time()
                                timestamp = datetime.datetime.now().strftime('%H%M%S')
                                filename = recording_dir / f"motion_{timestamp}_chunk{chunk_counter:03d}.mp4"
                                print(f"{thread_name} Recording final chunk {chunk_counter}: {filename}")
                                height, width, _ = post_frame.shape
                                temp_video_file = cv2.VideoWriter(str(filename), cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))
                        
                        motion_detected = False
                        if temp_video_file: temp_video_file.release(); temp_video_file = None
                        if recording_process: recording_process.terminate(); recording_process.wait(); recording_process = None
                        chunk_start_time = None
                        chunk_counter = 0
                        print(f"{thread_name} Recording session completed with {chunk_counter if chunk_counter > 0 else 1} chunk(s)")

                gray1 = gray2
            
            # Adaptive sleep and performance stats
            time.sleep(ADAPTIVE_SLEEP_MOTION if motion_detected else 
                      ADAPTIVE_SLEEP_NO_MOTION * (2 if consecutive_no_motion_frames > 30 else 1))
            
            current_time = time.time()
            if current_time - last_stats_time >= 30:
                elapsed = current_time - start_time
                fps_actual = frame_count / elapsed if elapsed > 0 else 0
                detection_fps = frames_processed_for_detection / elapsed if elapsed > 0 else 0
                try:
                    print(f"{thread_name} Performance: {fps_actual:.1f} FPS total, {detection_fps:.1f} detection FPS, CPU: {psutil.cpu_percent():.1f}%")
                except:
                    print(f"{thread_name} Performance: {fps_actual:.1f} FPS total, {detection_fps:.1f} detection FPS")
                last_stats_time = current_time

    except KeyboardInterrupt:
        print(f"{thread_name} Interrupted by user")
    except Exception as e:
        print(f"{thread_name} Error: {e}")
    finally:
        print(f"{thread_name} Cleaning up...")
        if temp_video_file: temp_video_file.release()
        if recording_process: 
            recording_process.terminate()
            recording_process.wait()
        cap.release()
        print(f"{thread_name} Done.")

def load_camera_config(config_file):
    """Load camera configuration from JSON file"""
    try:
        with open(config_file, 'r') as f: return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Config error: {e}")
        return None

def run_multiple_cameras(cameras_config):
    """Run motion detection for multiple cameras"""
    threads, stop_event = [], threading.Event()
    print(f"Starting motion detection for {len(cameras_config)} cameras...")
    
    for camera in cameras_config:
        camera_id, rtsp_url = camera['camera_id'], camera['url']
        thread = threading.Thread(
            target=detect_motion_record,
            args=(rtsp_url, camera_id, DEFAULT_THRESHOLD, DEFAULT_MIN_AREA, SKIP_FRAMES, 
                  DEFAULT_PRE_BUFFER_SECONDS, DEFAULT_POST_BUFFER_SECONDS, stop_event),
            name=f"Camera-{camera_id}", daemon=True)
        thread.start()
        threads.append(thread)
        print(f"Started thread for camera {camera_id}")
        time.sleep(2)
    
    try:
        # Wait for all threads or keyboard interrupt
        while any(thread.is_alive() for thread in threads):
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nReceived interrupt signal, stopping all cameras...")
        stop_event.set()
        for thread in threads:
            thread.join(timeout=5)
            if thread.is_alive():
                print(f"Warning: Thread {thread.name} did not stop gracefully")
        
        print("All camera threads stopped.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RTSP Motion Detection + Recording (JSON Config)")
    parser.add_argument("--config", default="config.json", help="JSON configuration file (default: config.json)")
    args = parser.parse_args()
    
    config = load_camera_config(args.config)
    if not config or not isinstance(config, list):
        print(f"Failed to load valid camera array from {args.config}")
        exit(1)
    
    print(f"Loaded configuration with {len(config)} cameras")
    run_multiple_cameras(config)