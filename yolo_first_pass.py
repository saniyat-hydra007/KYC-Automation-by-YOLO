from ultralytics import YOLO
import cv2
import os
import numpy as np
import shutil
import torch
import pandas as pd
import re

print(torch.__version__)
print(torch.cuda.is_available())
print(torch.cuda.get_device_name(0))

# Load model with CUDA
model = YOLO('yolov8n.pt').cuda()

# Base KYC folder path
kyc_folder = r"D:\Saniyat\Saniyat_s CODE\KYC Automation TEST\KYC"
evidence_base_folder = r"D:\Saniyat\Saniyat_s CODE\KYC Automation TEST\evidence"

# Load the CSV file
csv_path = r"D:\Saniyat\Saniyat_s CODE\KYC Automation TEST\KYC Video Verdict.csv"
kyc_verdict_df = pd.read_csv(csv_path)

def is_document_image(frame, box, min_area=1000, aspect_ratio_range=(0.7, 1.5), uniformity_threshold=5.0, text_threshold=0.35):
    x1, y1, x2, y2 = box
    width = x2 - x1
    height = y2 - y1
    area = width * height
    aspect_ratio = width / height if height > 0 else 1.0

    if area < min_area or not (aspect_ratio_range[0] <= aspect_ratio <= aspect_ratio_range[1]):
        return True

    crop = frame[y1:y2, x1:x2]
    if crop.size == 0:
        return False

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    std_val = np.std(gray)
    if std_val < uniformity_threshold:
        return True

    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    hsv_std = np.std(hsv[:, :, 1])
    if hsv_std < 20:
        return True

    edges = cv2.Canny(gray, 100, 200)
    edge_density = np.sum(edges) / (crop.shape[0] * crop.shape[1])
    if edge_density > 50:
        horizontal_edges = cv2.reduce(edges, 1, cv2.REDUCE_SUM, dtype=cv2.CV_32F)
        text_density = np.mean(horizontal_edges) / 255
        if text_density > text_threshold:
            return True

    return False

def evaluate_basic_quality(image_path, box):
    frame = cv2.imread(image_path)
    if frame is None:
        return 0

    x1, y1, x2, y2 = box
    padding = 20
    x1 = max(0, x1 - padding)
    y1 = max(0, y1 - padding)
    x2 = min(frame.shape[1], x2 + padding)
    y2 = min(frame.shape[0], y2 + padding)
    face_region = frame[y1:y2, x1:x2]

    if face_region.size == 0:
        return 0

    gray = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
    brightness = np.mean(gray)
    return brightness

# Function to validate email-like folder names
def is_email_folder(folder_name):
    return '@' in folder_name and '.' in folder_name and not any(part in folder_name for part in ['_Clean', '_Flagged'])

# Navigate through KYC folder and process only email-like folders
for email_folder in os.listdir(kyc_folder):
    email_path = os.path.join(kyc_folder, email_folder)
    if os.path.isdir(email_path) and is_email_folder(email_folder):
        verdict_row = kyc_verdict_df[kyc_verdict_df['email'] == email_folder]
        if verdict_row.empty:
            status = "Clean"
        else:
            verdict = verdict_row['Video Verdict'].iloc[0]
            status = "Flagged" if pd.notna(verdict) and verdict.strip() != "" else "Clean"

        output_folder = os.path.join(evidence_base_folder, f"{email_folder}_{status}")
        os.makedirs(output_folder, exist_ok=True)

        for file_name in os.listdir(email_path):
            if file_name.endswith(('.webm', '.mp4')):
                video_path = os.path.join(email_path, file_name)
                cap = cv2.VideoCapture(video_path)
                assert cap.isOpened(), f"Error reading video file: {video_path}"

                # Get video properties
                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                print(f"Processing video: {video_path} (Status: {status}, FPS: {fps}, Total Frames: {frame_count})")

                seen_ids = set()
                frame_count_processed = 0
                temp_folders = {}
                track_id_frames = {}  # Store (frame_path, box) for each track_id
                person_detected = False  # Flag to track if any person is detected

                # Process every frame
                while cap.isOpened():
                    success, frame = cap.read()
                    if not success:
                        break

                    frame_count_processed += 1
                    print(f"Processing frame {frame_count_processed}")

                    results = model.track(frame, conf=0.25, iou=0.25, persist=True)
                    annotated_frame = results[0].plot()
                    cv2.imwrite(os.path.join(output_folder, f"annotated_frame_{frame_count_processed}.jpg"), annotated_frame)

                    if results[0].boxes is not None:
                        boxes = results[0].boxes.xyxy.int().tolist()
                        class_ids = results[0].boxes.cls.int().tolist()

                        if hasattr(results[0].boxes, 'id') and results[0].boxes.id is not None:
                            track_ids = results[0].boxes.id.int().tolist()
                        else:
                            track_ids = [None] * len(boxes)

                        detected_ids = [tid for tid, cls_id in zip(track_ids, class_ids) if tid is not None and cls_id == 0]
                        print(f"Frame {frame_count_processed}: Detected track IDs: {detected_ids}")

                        if detected_ids:  # If any person is detected
                            person_detected = True

                        for box, cls_id, track_id in zip(boxes, class_ids, track_ids):
                            if track_id is None:
                                continue

                            if cls_id == 0:  # Person class
                                x1, y1, x2, y2 = box
                                box_center = ((x1 + x2) // 2, (y1 + y2) // 2)

                                if is_document_image(frame, box):
                                    print(f"Skipped ID {track_id} as document image at {box_center}")
                                    continue

                                # Ensure unique tracking by comparing bounding box positions
                                if track_id not in seen_ids:
                                    seen_ids.add(track_id)
                                    print(f"New person detected with ID: {track_id} at {box_center}")
                                    temp_folder = os.path.join(output_folder, f"temp_id_{track_id}")
                                    os.makedirs(temp_folder, exist_ok=True)
                                    temp_folders[track_id] = temp_folder
                                    track_id_frames[track_id] = []

                                temp_folder = temp_folders[track_id]
                                frame_filename = os.path.join(temp_folder, f"face_frame_{frame_count_processed}.jpg")
                                cv2.imwrite(frame_filename, frame)
                                print(f"Saved frame {frame_count_processed} for ID {track_id} to {frame_filename}")

                                # Store the frame path and its bounding box
                                track_id_frames[track_id].append((frame_filename, box))

                cap.release()

                # Select the best frame for each tracked person
                for track_id in seen_ids:
                    temp_folder = temp_folders[track_id]
                    best_brightness = 0
                    best_frame_path = None
                    best_box = None

                    # Evaluate brightness for each frame using its specific bounding box
                    for frame_path, box in track_id_frames[track_id]:
                        brightness = evaluate_basic_quality(frame_path, box)
                        if brightness > best_brightness:
                            best_brightness = brightness
                            best_frame_path = frame_path
                            best_box = box

                    if best_frame_path:
                        final_filename = os.path.join(output_folder, f"person_{track_id}_{status}.jpg")
                        shutil.copy(best_frame_path, final_filename)
                        print(f"Selected best frame for ID {track_id}: {best_frame_path} with brightness {best_brightness}, saved as {final_filename}")
                    else:
                        if track_id_frames[track_id]:
                            fallback_path, fallback_box = track_id_frames[track_id][0]
                            final_filename = os.path.join(output_folder, f"person_{track_id}_{status}.jpg")
                            shutil.copy(fallback_path, final_filename)
                            print(f"No suitable frame found for ID {track_id}, saved fallback frame: {fallback_path} as {final_filename}")

                    shutil.rmtree(temp_folder)
                    print(f"Cleaned up temp folder: {temp_folder}")

                # Mark video as glitched if no person is detected
                if not person_detected:
                    glitched_file = os.path.join(output_folder, f"{os.path.splitext(file_name)[0]}_glitched.txt")
                    with open(glitched_file, 'w') as f:
                        f.write("No person face detected in video frames.")
                    print(f"Marked video {file_name} as glitched due to no person detection.")
                    
cv2.imwrite(os.path.join(output_folder, f"annotated_frame_{frame_count}.jpg"), annotated_frame)
cv2.destroyAllWindows()