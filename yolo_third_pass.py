import os
import cv2
import numpy as np
import pandas as pd
from deepface import DeepFace
from ultralytics import YOLO

# Paths
evidence_folder = r"D:\Saniyat\Saniyat_s CODE\KYC Automation FLASK\evidence"
kyc_verdict_csv = r"D:\Saniyat\Saniyat_s CODE\KYC Automation FLASK\KYC Video Verdict.csv"
input_csv = r"D:\Saniyat\Saniyat_s CODE\KYC Automation FLASK\evidence_status.csv"
output_csv = r"D:\Saniyat\Saniyat_s CODE\KYC Automation FLASK\evidence_status_updated.csv"

# Load YOLO model for detection
model = YOLO('yolov8n.pt').cuda()

# Function to detect faces using DeepFace
def has_face(image_path):
    try:
        result = DeepFace.detectFace(image_path, detector_backend="opencv", enforce_detection=False)
        return len(result) > 0
    except Exception as e:
        print(f"Error checking face in {os.path.basename(image_path)}: {str(e)}")
        return False

# Function to detect feet
def has_feet(image_path):
    image = cv2.imread(image_path)
    if image is None:
        return False
    results = model(image, conf=0.7)
    boxes = results[0].boxes.xyxy.int().tolist() if results[0].boxes is not None else []
    class_ids = results[0].boxes.cls.int().tolist() if results[0].boxes is not None else []
    for box, cls_id in zip(boxes, class_ids):
        if cls_id == 0:  # Person class
            x1, y1, x2, y2 = box
            if y2 > image.shape[0] * 0.7:  # Feet in bottom 30% of image
                return True
    return False

# Function to check if feet belong to another person
def different_person_feet(image_path1, image_path2):
    img1 = cv2.imread(image_path1)
    img2 = cv2.imread(image_path2)
    if img1 is None or img2 is None:
        return False
    
    results1 = model(img1, conf=0.7)
    results2 = model(img2, conf=0.7)
    
    boxes1 = results1[0].boxes.xyxy.int().tolist() if results1[0].boxes is not None else []
    boxes2 = results2[0].boxes.xyxy.int().tolist() if results2[0].boxes is not None else []
    class_ids1 = results1[0].boxes.cls.int().tolist() if results1[0].boxes is not None else []
    class_ids2 = results2[0].boxes.cls.int().tolist() if results2[0].boxes is not None else []
    
    person_boxes1 = [box for box, cls_id in zip(boxes1, class_ids1) if cls_id == 0 and has_feet(image_path1)]
    person_boxes2 = [box for box, cls_id in zip(boxes2, class_ids2) if cls_id == 0 and has_feet(image_path2)]
    
    if not person_boxes1 or not person_boxes2:
        return False
    
    for box1 in person_boxes1:
        for box2 in person_boxes2:
            iou = calculate_iou(box1, box2)
            if iou < 0.3:  # Low IoU suggests different persons
                return True
    return False

# Function to calculate IoU
def calculate_iou(box1, box2):
    x1_1, y1_1, x2_1, y2_1 = box1
    x1_2, y1_2, x2_2, y2_2 = box2
    x1_i = max(x1_1, x1_2)
    y1_i = max(y1_1, y1_2)
    x2_i = min(x2_1, x2_2)
    y2_i = min(y2_1, y2_2)
    intersection = max(0, x2_i - x1_i) * max(0, y2_i - y1_i)
    area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
    area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
    union = area1 + area2 - intersection
    return intersection / union if union > 0 else 0

# Load the existing CSVs
try:
    df = pd.read_csv(input_csv)
    kyc_df = pd.read_csv(kyc_verdict_csv)
except FileNotFoundError as e:
    print(f"Error: {e}")
    exit()

# Preserve the original status column from evidence_status.csv
df['Original Status'] = df['status']

# Merge KYC Video Verdict with the input DataFrame
df = df.merge(kyc_df[['email', 'Video Verdict']], on='email', how='left')
df['Video Verdict'] = df['Video Verdict'].fillna('No Media Found')
df = df.drop(columns=['status'])  # Remove the original status column after preserving it

# Restore 'video glitched' from Original Status if it was overwritten
df.loc[df['Original Status'].str.lower() == 'video glitched', 'Video Verdict'] = 'video glitched'

# Drop the temporary Original Status column
df = df.drop(columns=['Original Status'])

# Re-evaluate only folders where Video Verdict is not 'No Media Found' or 'video glitched'
for i, row in df.iterrows():
    if row['Video Verdict'].lower() in ['no media found', 'video glitched']:
        continue
    
    email_folder = row['email']
    # Check for both _Clean and _Flagged folders
    possible_folders = [f"{email_folder}_Clean", f"{email_folder}_Flagged"]
    email_path = None
    for folder in possible_folders:
        path = os.path.join(evidence_folder, folder)
        if os.path.isdir(path):
            email_path = path
            break
    
    if not email_path:
        print(f"Folder for {email_folder} not found, marking as No Media Found")
        df.at[i, 'Video Verdict'] = 'No Media Found'
        continue
    
    # Get all person images in evidence
    person_images = [f for f in os.listdir(email_path) if f.startswith('person_') and f.endswith('.jpg')]
    
    if len(person_images) <= 1:
        print(f"Folder {email_folder} has 0 or 1 images, updating to clean")
        df.at[i, 'Video Verdict'] = 'clean'
        continue
    
    # Check for face and feet combination
    has_face_image = any(has_face(os.path.join(email_path, img)) for img in person_images)
    has_feet_image = any(has_feet(os.path.join(email_path, img)) for img in person_images)
    
    # Check for different person feet
    different_feet = False
    for j in range(len(person_images)):
        for k in range(j + 1, len(person_images)):
            img1_path = os.path.join(email_path, person_images[j])
            img2_path = os.path.join(email_path, person_images[k])
            if has_feet(img1_path) and has_feet(img2_path):
                if different_person_feet(img1_path, img2_path):
                    different_feet = True
                    break
        if different_feet:
            break
    
    # Update Video Verdict
    if (has_face_image and has_feet_image) or different_feet:
        print(f"Folder {email_folder} contains face and feet or different person feet, marking as flagged")
        df.at[i, 'Video Verdict'] = 'flagged'
    else:
        print(f"Folder {email_folder} does not meet flagged criteria, marking as clean")
        df.at[i, 'Video Verdict'] = 'clean'

# Save updated DataFrame to CSV
df.to_csv(output_csv, index=False)
print(f"Updated evidence status saved to {output_csv}")
print(df)