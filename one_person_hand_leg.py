from ultralytics import YOLO
import cv2
import os
import numpy as np

# Load YOLO model
model = YOLO('yolov8n.pt')

# Load Haar Cascade for face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Evidence folder path
evidence_base_folder = r"D:\Saniyat\Saniyat_s CODE\KYC Automation FLASK\evidence"

def detect_face(image):
    """Detect if a face is present in the image."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    return len(faces) > 0

def detect_hands_or_feet(image):
    """Detect hands or feet using YOLO with improved heuristics for a single limb."""
    results = model(image, conf=0.25, iou=0.25)
    boxes = results[0].boxes.xyxy.int().tolist()
    class_ids = results[0].boxes.cls.int().tolist()

    limb_count = 0
    img_height, img_width = image.shape[:2]

    for box, cls_id in zip(boxes, class_ids):
        if cls_id == 0:  # Person class
            x1, y1, x2, y2 = box
            width = x2 - x1
            height = y2 - y1
            area = width * height
            center_y = (y1 + y2) / 2

            # Heuristic for hands: smaller area, upper/middle part of the frame
            if area < (img_width * img_height * 0.1) and center_y < img_height * 0.7:
                limb_count += 1
                print(f"Detected hand in box {box}")
                continue

            # Heuristic for feet: bottom part of the frame, any reasonable size
            if center_y > img_height * 0.7 and height > 20:  # Minimum height to avoid noise
                limb_count += 1
                print(f"Detected foot in box {box}")
                continue

    # Return True if exactly one limb (hand or foot) is detected
    return limb_count == 1

def process_person_images():
    """Process person_*.jpg images in the evidence folder and delete those with only one hand or foot."""
    for folder_name in os.listdir(evidence_base_folder):
        folder_path = os.path.join(evidence_base_folder, folder_name)
        if os.path.isdir(folder_path):
            images_to_delete = []

            # Process only person_*.jpg images
            for file_name in os.listdir(folder_path):
                if file_name.startswith('person_') and file_name.endswith('.jpg'):
                    image_path = os.path.join(folder_path, file_name)
                    image = cv2.imread(image_path)
                    if image is not None:
                        has_face = detect_face(image)
                        has_only_one_limb = detect_hands_or_feet(image)

                        if not has_face and has_only_one_limb:
                            print(f"Deleting {image_path} as it contains only one hand or foot without a face")
                            images_to_delete.append(image_path)
                        else:
                            print(f"Keeping {image_path} as it contains a face or does not meet deletion criteria")

            # Delete marked images
            for image_path in images_to_delete:
                if os.path.exists(image_path):
                    os.remove(image_path)
                    print(f"Deleted {image_path}")

if __name__ == "__main__":
    process_person_images()
    cv2.destroyAllWindows()