import os

# Base evidence folder path
evidence_folder = r"D:\Saniyat\Saniyat_s CODE\KYC Automation TEST\evidence"

# Navigate through each folder in the evidence directory
for folder_name in os.listdir(evidence_folder):
    folder_path = os.path.join(evidence_folder, folder_name)
    if os.path.isdir(folder_path):
        print(f"Processing folder: {folder_name}")
        
        # Navigate through all files in the current folder
        for file_name in os.listdir(folder_path):
            if file_name.startswith("annotated_frame") and file_name.endswith(".jpg"):
                file_path = os.path.join(folder_path, file_name)
                try:
                    os.remove(file_path)
                    print(f"Deleted: {file_name} from {folder_name}")
                except Exception as e:
                    print(f"Error deleting {file_name} from {folder_name}: {str(e)}")

print("Cleanup of annotated frames completed.")