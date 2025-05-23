import cv2
import torch
import os
from datetime import datetime
from config import Config
import numpy as np

model = torch.hub.load('ultralytics/yolov5', 'yolov5m', pretrained=True)

def analyze_video(video_path, email):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = 0
    results = {
        'email': email,
        'detected': False,
        'status': 'Single Person',
        'detection_time': None,  # Changed from 'timestamp' to 'detection_time'
        'evidence_path': None
    }
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_count % Config.FRAME_RATE == 0:
            current_time = frame_count / fps
            
            # Detection logic
            results_det = model(frame)
            persons = results_det.pandas().xyxy[0][results_det.pandas().xyxy[0]['class'] == 0]
            
            if len(persons) >= 2:
                # Draw bounding boxes
                for _, det in persons.iterrows():
                    x1, y1, x2, y2 = map(int, det[['xmin', 'ymin', 'xmax', 'ymax']])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, f"Person {det['confidence']:.2f}", 
                               (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 
                               0.5, (0, 255, 0), 2)
                
                # Save evidence with video timestamp only
                timestamp_str = f"{current_time:.2f}s"
                results.update({
                    'detected': True,
                    'status': f'Multiple Persons at {timestamp_str}',
                    'detection_time': timestamp_str,  # Only store video timestamp
                    'evidence_path': save_evidence(frame, email, current_time)
                })
                break
        
        frame_count += 1
    
    cap.release()
    return results

def save_evidence(frame, email, video_timestamp):
    """Save with email and video timestamp only"""
    os.makedirs(Config.EVIDENCE_FOLDER, exist_ok=True)
    filename = f"{email}_{video_timestamp:.2f}s.jpg".replace('.', '_')
    path = os.path.join(Config.EVIDENCE_FOLDER, filename)
    cv2.imwrite(path, frame)
    return path

def process_all_videos():
    results = []
    for root, _, files in os.walk(Config.UPLOAD_FOLDER):
        for file in files:
            if file.endswith(('.webm', '.mp4')):
                email = os.path.basename(root)
                video_path = os.path.join(root, file)
                results.append(analyze_video(video_path, email))
    return results