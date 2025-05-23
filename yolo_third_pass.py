import os
import cv2
import numpy as np
import pandas as pd
from deepface import DeepFace
from ultralytics import YOLO
from datetime import datetime

# Paths
evidence_folder = r"D:\Saniyat\Saniyat_s CODE\KYC Automation TEST\evidence"
kyc_verdict_csv = r"D:\Saniyat\Saniyat_s CODE\KYC Automation TEST\KYC Video Verdict.csv"
input_csv = r"D:\Saniyat\Saniyat_s CODE\KYC Automation TEST\evidence_status.csv"
output_csv = r"D:\Saniyat\Saniyat_s CODE\KYC Automation TEST\evidence_status_updated_version.csv"
log_file_path = r"D:\Saniyat\Saniyat_s CODE\KYC Automation TEST\logs\processing_log.txt"

# Ensure the logs directory exists
log_dir = os.path.dirname(log_file_path)
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Function to log messages with timestamp
def log_message(message):
    timestamp = datetime.now().strftime("%I:%M %p +06 on %A, %B %d, %Y")
    log_entry = f"{timestamp} - {message}\n"
    with open(log_file_path, 'a') as log_file:
        log_file.write(log_entry)
    print(message)

# Load YOLO model for detection
model = YOLO('yolov8n.pt').cuda()

def is_document_image(image, box, min_area=1500, aspect_ratio_range=(1.5, 1.65), uniformity_threshold=5.0, text_threshold=0.4, edge_density_threshold=50, hough_line_threshold=40, frame_proportion_threshold=0.25):
    x1, y1, x2, y2 = box
    width = x2 - x1
    height = y2 - y1
    area = width * height
    aspect_ratio = width / height if height > 0 else 1.0

    frame_area = image.shape[0] * image.shape[1]
    frame_proportion = area / frame_area if frame_area > 0 else 0
    if frame_proportion > frame_proportion_threshold:
        return False

    if area < min_area or not (aspect_ratio_range[0] <= aspect_ratio <= aspect_ratio_range[1]):
        return True

    crop = image[y1:y2, x1:x2]
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

    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    text_density = sum(cv2.contourArea(c) for c in contours if 50 < cv2.contourArea(c) < 500) / (width * height) if (width * height) > 0 else 0
    if text_density > text_threshold:
        return True

    edges = cv2.Canny(gray, 100, 200)
    edge_density = np.sum(edges) / (crop.shape[0] * crop.shape[1])
    if edge_density > edge_density_threshold:
        return True

    lines = cv2.HoughLines(edges, 1, np.pi / 180, hough_line_threshold)
    if lines is not None and len(lines) > 2:
        return True

    hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
    contrast_ratio = (np.sum(hist[0:50]) + np.sum(hist[200:256])) / np.sum(hist) if np.sum(hist) > 0 else 0
    if contrast_ratio > 0.6:
        return True

    return False

def has_face(image_path):
    try:
        faces = DeepFace.extract_faces(image_path, detector_backend="mtcnn", enforce_detection=False)
        return len(faces) > 0
    except Exception as e:
        error_msg = f"Error checking face in {os.path.basename(image_path)}: {str(e)}"
        log_message(error_msg)
        return False

def has_feet(image_path):
    image = cv2.imread(image_path)
    if image is None:
        return False
    results = model(image, conf=0.7)
    boxes = results[0].boxes.xyxy.int().tolist() if results[0].boxes is not None else []
    class_ids = results[0].boxes.cls.int().tolist() if results[0].boxes is not None else []
    foot_count = 0
    for box, cls_id in zip(boxes, class_ids):
        if cls_id == 0:
            if is_document_image(image, box):
                continue
            x1, y1, x2, y2 = box
            height = y2 - y1
            lower_third_y = y1 + 2 * (height // 3)
            if y2 >= lower_third_y:
                foot_count += 1
    return foot_count > 0 and foot_count < 3  # Allow up to 2 feet to avoid flagging full person

def compare_faces(image_path1, image_path2):
    try:
        result = DeepFace.verify(image_path1, image_path2, model_name="Facenet512", distance_metric="cosine", enforce_detection=False, threshold=0.7)
        return result["verified"]
    except Exception as e:
        error_msg = f"Error comparing faces between {os.path.basename(image_path1)} and {os.path.basename(image_path2)}: {str(e)}"
        log_message(error_msg)
        # Fallback: Compare based on bounding box similarity if face verification fails
        img1 = cv2.imread(image_path1)
        img2 = cv2.imread(image_path2)
        if img1 is None or img2 is None:
            return False
        results1 = model(img1, conf=0.7)
        results2 = model(img2, conf=0.7)
        if results1[0].boxes is None or results2[0].boxes is None:
            return False
        box1 = results1[0].boxes.xyxy.int().tolist()[0]
        box2 = results2[0].boxes.xyxy.int().tolist()[0]
        area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
        area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
        area_diff = abs(area1 - area2) / max(area1, area2) if max(area1, area2) > 0 else 1
        return area_diff < 0.4  # Threshold for similar bounding box size
    return False

# Load the existing CSVs
try:
    df = pd.read_csv(input_csv)
    kyc_df = pd.read_csv(kyc_verdict_csv)
except FileNotFoundError as e:
    error_msg = f"Error loading CSVs: {str(e)}"
    log_message(error_msg)
    exit()

df['Original Status'] = df['status']
df = df.merge(kyc_df[['email', 'Video Verdict']], on='email', how='left')
df['Video Verdict'] = df['Video Verdict'].fillna('No Media Found')
df.loc[df['Original Status'].str.lower() == 'video glitched', 'Video Verdict'] = 'video glitched'
df = df.drop(columns=['status', 'Original Status'])

for i, row in df.iterrows():
    if row['Video Verdict'].lower() in ['no media found', 'video glitched']:
        continue
    
    email_folder = row['email']
    possible_folders = [f"{email_folder}_Clean", f"{email_folder}_Flagged"]
    email_path = None
    for folder in possible_folders:
        path = os.path.join(evidence_folder, folder)
        if os.path.isdir(path):
            email_path = path
            break
    
    if not email_path:
        msg = f"Folder for {email_folder} not found, marking as No Media Found"
        log_message(msg)
        df.at[i, 'Video Verdict'] = 'No Media Found'
        continue
    
    person_images = [f for f in os.listdir(email_path) if "person" in f and f.endswith('.jpg')]
    
    if not person_images:
        msg = f"Folder {email_folder} has no person images, marking as flagged"
        log_message(msg)
        df.at[i, 'Video Verdict'] = 'flagged'
        continue
    
    images_with_faces = []
    for img in person_images:
        img_path = os.path.join(email_path, img)
        image = cv2.imread(img_path)
        if image is None:
            msg = f"Failed to load image {img} in {email_folder}"
            log_message(msg)
            continue
        
        results = model(image, conf=0.5)  # Increased confidence to reduce false positives
        if results[0].boxes is None:
            continue
        
        boxes = results[0].boxes.xyxy.int().tolist()
        class_ids = results[0].boxes.cls.int().tolist()
        
        person_detected = False
        for box, cls_id in zip(boxes, class_ids):
            if cls_id == 0:
                if is_document_image(image, box):
                    msg = f"Skipped {img} as document image in {email_folder}"
                    log_message(msg)
                    continue
                person_detected = True
                break
        
        if not person_detected:
            continue
        
        if has_face(img_path):
            images_with_faces.append(img)
        else:
            msg = f"No human face detected in {img} in {email_folder}"
            log_message(msg)
    
    if not images_with_faces:
        msg = f"Folder {email_folder} has no human faces in person images, marking as flagged"
        log_message(msg)
        df.at[i, 'Video Verdict'] = 'flagged'
        continue
    
    if len(images_with_faces) == 1:
        msg = f"Folder {email_folder} has exactly one person image with a face, marking as clean"
        log_message(msg)
        df.at[i, 'Video Verdict'] = 'clean'
        continue
    
    has_feet_image = any(has_feet(os.path.join(email_path, img)) for img in images_with_faces)
    
    person_groups = []
    for img in images_with_faces:
        img_path = os.path.join(email_path, img)
        person_id = int(img.split('_')[1])
        matched = False
        for group in person_groups:
            group_leader = group[0]
            leader_path = os.path.join(email_path, f"person_{group_leader}_Clean.jpg")
            if compare_faces(img_path, leader_path):
                group.append(person_id)
                matched = True
                break
        if not matched:
            person_groups.append([person_id])
    
    if len(person_groups) > 1:
        msg = f"Folder {email_folder} has multiple distinct persons ({len(person_groups)} groups), marking as flagged"
        log_message(msg)
        df.at[i, 'Video Verdict'] = 'flagged'
    elif has_feet_image:
        msg = f"Folder {email_folder} contains face and feet, marking as flagged"
        log_message(msg)
        df.at[i, 'Video Verdict'] = 'flagged'
    else:
        msg = f"Folder {email_folder} has only one person group without feet, marking as clean"
        log_message(msg)
        df.at[i, 'Video Verdict'] = 'clean'

df.to_csv(output_csv, index=False)
final_msg = f"Updated evidence status saved to {output_csv}"
log_message(final_msg)
print(df)