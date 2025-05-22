## 1. Make Sure Python is Installed
python3 --version

### If not installed
sudo apt install python3 python3-pip -y

## 2. Create a Virtual Environment
python3 -m venv venv

## 3.  Activate the Environment
source venv/bin/activate

## 4. Install Required Python Packages
pip3 install opencv-python numpy

## 5. Run command
python3 your_script.py --url "rtsp://admin:123456@10.1.4.18:8554/ch01" --skip-frames 10
