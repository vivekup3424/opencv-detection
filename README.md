## 1. Make Sure Python is Installed
python3 --version

### If not installed
sudo apt install python3 python3-pip -y

## 2. Create a Virtual Environment
python3 -m venv venv

## 3.  Activate the Environment
source venv/bin/activate

## 4. Install Required Python Packages
pip3 install opencv-python numpy psutil

## 5. Run Motion Detection

### Default Configuration
```bash
# Uses config.json by default
python3 motion-ffmpeg.py
```

### Custom Configuration File
```bash
python3 motion-ffmpeg.py --config my-config.json
```

## Configuration File (config.json)

### Multi-Camera Configuration
```json
[
  {
    "camera_id": "front_door",
    "url": "rtsp://admin:password@192.168.1.100:554/stream1",
    "threshold": 25,
    "min_area": 500
  },
  {
    "camera_id": "backyard",
    "url": "rtsp://admin:password@192.168.1.101:554/stream1",
    "threshold": 30,
    "min_area": 600
  }
]
```

### Single Camera Configuration
```json
{
  "camera_id": "workbench",
  "url": "rtsp://admin:password@192.168.1.105:554/stream1",
  "threshold": 20,
  "min_area": 300
}
```

## Configuration Parameters

### Per-Camera Settings (optional, uses defaults from Python constants if not specified)
- `camera_id`: Unique identifier for the camera (required)
- `url`: RTSP stream URL (required)
- `threshold`: Motion detection sensitivity (optional, default: 25)
- `min_area`: Minimum area for motion detection (optional, default: 500)

### Default Settings (defined as constants in motion-ffmpeg.py)
- `SKIP_FRAMES = 10`: Process every 10th frame
- `DEFAULT_PRE_BUFFER_SECONDS = 5`: Record 5 seconds before motion
- `DEFAULT_POST_BUFFER_SECONDS = 5`: Record 5 seconds after motion
- `CHUNK_DURATION_SECONDS = 60`: Max 60-second video chunks
- `CLEANUP_DAYS = 3`: Keep recordings for 3 days

## Features
- **Multi-camera support**: Monitor multiple RTSP streams simultaneously
- **1-minute chunk recording**: Automatic file splitting for long motion events
- **Pre/post buffer**: Records 5 seconds before and after motion detection
- **Organized storage**: `recordings/{camera_id}/{date}/` structure
- **Automatic cleanup**: Removes recordings older than 3 days
- **CPU optimized**: Reduced resolution motion detection, adaptive sleep
- **Thread-safe**: Each camera runs in its own thread
