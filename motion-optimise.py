import cv2
import time
import datetime
import argparse
import sys

def detect_motion(rtsp_url, threshold=25, min_area=500, display=False, frame_skip=2):
    print(f"Connecting to RTSP stream: {rtsp_url}")
    cap = cv2.VideoCapture(rtsp_url)

    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'H264'))
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)   # Reduce resolution
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
    cap.set(cv2.CAP_PROP_FPS, 10)            # Limit FPS if supported

    time.sleep(2)
    if not cap.isOpened():
        print("Error: Could not open RTSP stream")
        return

    print("Stream opened successfully")

    for _ in range(50):
        ret, frame1 = cap.read()
        if ret:
            break
        time.sleep(0.1)

    if not ret:
        print("Failed to get initial frame")
        return

    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray1 = cv2.GaussianBlur(gray1, (11, 11), 0)  # Smaller kernel for speed

    motion_detected = False
    last_motion_time = None
    frame_count = 0

    try:
        while True:
            ret, frame2 = cap.read()
            if not ret:
                print("Failed to read frame")
                break

            frame_count += 1
            if frame_count % frame_skip != 0:
                continue  # Skip frame to reduce CPU

            gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.GaussianBlur(gray2, (11, 11), 0)

            frame_delta = cv2.absdiff(gray1, gray2)
            thresh = cv2.threshold(frame_delta, threshold, 255, cv2.THRESH_BINARY)[1]
            thresh = cv2.dilate(thresh, None, iterations=1)

            contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            motion_this_frame = False
            for contour in contours:
                if cv2.contourArea(contour) < min_area:
                    continue
                motion_this_frame = True
                if display:
                    (x, y, w, h) = cv2.boundingRect(contour)
                    cv2.rectangle(frame2, (x, y), (x + w, y + h), (0, 255, 0), 2)

            if motion_this_frame:
                if not motion_detected:
                    motion_detected = True
                    print(f"Motion detected at {datetime.datetime.now()}")
                last_motion_time = time.time()
            elif motion_detected and time.time() - last_motion_time > 2:
                motion_detected = False
                print(f"Motion stopped at {datetime.datetime.now()}")

            if display:
                cv2.imshow("Motion", frame2)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            gray1 = gray2

    except KeyboardInterrupt:
        print("Stopped by user")
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--threshold", type=int, default=25)
    parser.add_argument("--min-area", type=int, default=500)
    parser.add_argument("--display", action="store_true")
    parser.add_argument("--frame-skip", type=int, default=2, help="Process every Nth frame")

    args = parser.parse_args()
    detect_motion(args.url, args.threshold, args.min_area, args.display, args.frame_skip)