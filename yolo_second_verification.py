#################################
#################################
#################################
import os
import cv2
import numpy as np
import pandas as pd
from deepface import DeepFace
from ultralytics import YOLO

# Paths
evidence_folder = r"D:\Saniyat\Saniyat_s CODE\KYC Automation FLASK\evidence"
output_csv = r"D:\Saniyat\Saniyat_s CODE\KYC Automation FLASK\evidence_status.csv"

# Load YOLO model for bounding box detection
model = YOLO('yolov8n.pt').cuda()

# Function to check if an image contains a face
def has_face(image_path):
    try:
        # Use DeepFace to detect a face
        analysis = DeepFace.analyze(img_path=image_path, actions=['emotion'], detector_backend='opencv', enforce_detection=False, silent=True)
        if analysis and len(analysis) > 0 and analysis[0].get('face_confidence', 0) > 0.8:
            return True
        return False
    except Exception as e:
        print(f"Error checking face in {os.path.basename(image_path)}: {str(e)}")
        return False

# Function to calculate IoU (Intersection over Union) for bounding boxes
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

# Function to compare two images using DeepFace
def are_same_person(image_path1, image_path2, iou_threshold=0.7):
    # Load images
    image1 = cv2.imread(image_path1)
    image2 = cv2.imread(image_path2)
    if image1 is None or image2 is None:
        print(f"Failed to load {os.path.basename(image_path1)} or {os.path.basename(image_path2)}")
        return True
    
    # Detect persons using YOLO
    results1 = model(image1, conf=0.7)
    results2 = model(image2, conf=0.7)
    
    boxes1 = results1[0].boxes.xyxy.int().tolist() if results1[0].boxes is not None else []
    boxes2 = results2[0].boxes.xyxy.int().tolist() if results2[0].boxes is not None else []
    class_ids1 = results1[0].boxes.cls.int().tolist() if results1[0].boxes is not None else []
    class_ids2 = results2[0].boxes.cls.int().tolist() if results2[0].boxes is not None else []
    
    person_boxes1 = [box for box, cls_id in zip(boxes1, class_ids1) if cls_id == 0]
    person_boxes2 = [box for box, cls_id in zip(boxes2, class_ids2) if cls_id == 0]
    
    if not person_boxes1 or not person_boxes2:
        print(f"No persons detected in {os.path.basename(image_path1)} or {os.path.basename(image_path2)}")
        return True
    
    max_iou = 0
    for box1 in person_boxes1:
        for box2 in person_boxes2:
            iou = calculate_iou(box1, box2)
            max_iou = max(max_iou, iou)
    
    if max_iou < iou_threshold:
        print(f"Low IoU ({max_iou}) between {os.path.basename(image_path1)} and {os.path.basename(image_path2)}")
        return True
    
    # Use DeepFace for face verification with ArcFace
    try:
        result = DeepFace.verify(img1_path=image_path1, img2_path=image_path2, model_name="ArcFace", detector_backend="opencv", distance_metric="cosine", enforce_detection=False)
        print(f"DeepFace verification result for {os.path.basename(image_path1)} and {os.path.basename(image_path2)}: {result['verified']} (distance: {result['distance']})")
        return result['verified']
    except Exception as e:
        print(f"DeepFace error for {os.path.basename(image_path1)} and {os.path.basename(image_path2)}: {str(e)}")
        return True

# DataFrame to store results
data = []

# Navigate through evidence folder
for email_folder in os.listdir(evidence_folder):
    email_path = os.path.join(evidence_folder, email_folder)
    if os.path.isdir(email_path):
        # Get all person images in evidence
        person_images = [f for f in os.listdir(email_path) if f.startswith('person_') and f.endswith('.jpg')]
        
        # Case 1: No images in folder
        if len(person_images) == 0:
            print(f"No person images found in evidence for {email_folder}, marking as video glitched")
            data.append({'email': email_folder, 'status': 'video glitched'})
            continue
        
        # Case 2: Only one image in folder
        if len(person_images) == 1:
            print(f"Only one person image found for {email_folder}, marking as clean")
            data.append({'email': email_folder, 'status': 'clean'})
            continue
        
        # Case 3: Check for body part vs face
        has_face_list = []
        for person_image in person_images:
            person_image_path = os.path.join(email_path, person_image)
            has_face_list.append(has_face(person_image_path))
        
        # If some images have faces and others don't, mark as flagged
        if any(has_face_list) and not all(has_face_list):
            print(f"Mix of face and non-face images detected in {email_folder}, marking as flagged")
            data.append({'email': email_folder, 'status': 'flagged'})
            continue
        
        # Case 4: Compare images within the folder to check if they are the same person
        all_same_person = True
        # Compare each pair of images
        for i in range(len(person_images)):
            for j in range(i + 1, len(person_images)):
                img1_path = os.path.join(email_path, person_images[i])
                img2_path = os.path.join(email_path, person_images[j])
                if not are_same_person(img1_path, img2_path):
                    all_same_person = False
                    break
            if not all_same_person:
                break
        
        status = 'clean' if all_same_person else 'flagged'
        print(f"All images in {email_folder} are {'the same' if all_same_person else 'not the same'}, marking as {status}")
        data.append({'email': email_folder, 'status': status})

# Create DataFrame and save to CSV
df = pd.DataFrame(data)
df.to_csv(output_csv, index=False)
print(f"Evidence status saved to {output_csv}")
print(df)