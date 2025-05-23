import os
import shutil

# List of paths to delete (including the new log file)
paths_to_delete = [
    r"/home/ubuntu/KYC-Automation-by-YOLO/evidence",
    r"/home/ubuntu/KYC-Automation-by-YOLO/KYC",
    r"/home/ubuntu/KYC-Automation-by-YOLO/evidence_status_updated_hand_feet.csv",
    r"/home/ubuntu/KYC-Automation-by-YOLO/evidence_status_updated.csv",
    r"/home/ubuntu/KYC-Automation-by-YOLO/evidence_status.csv",
    r"/home/ubuntu/KYC-Automation-by-YOLO/KYC_Video_Verdict.csv",
    r"/home/ubuntu/KYC-Automation-by-YOLO/validation_result.csv",
    r"/home/ubuntu/KYC-Automation-by-YOLO/app_execution.log",  # Newly added log file
    r"/home/ubuntu/KYC-Automation-by-YOLO/evidence_status_updated_version.csv",
    r"/home/ubuntu/KYC-Automation-by-YOLO/logs/processing_log.txt"
]

def delete_paths(path_list):
    for path in path_list:
        if os.path.exists(path):
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                    print(f"[+] Deleted folder: {path}")
                else:
                    os.remove(path)
                    print(f"[+] Deleted file: {path}")
            except Exception as e:
                print(f"[!] Error deleting {path}: {e}")
        else:
            print(f"[-] Path not found (skipped): {path}")

if __name__ == "__main__":
    print("This script will delete the following files/folders:")
    for path in paths_to_delete:
        print(f" - {path}")
    
    confirm = input("\nAre you sure you want to continue? (y/n): ").strip().lower()
    if confirm == 'y':
        delete_paths(paths_to_delete)
        print("\nCleanup completed.")
    else:
        print("Operation cancelled.")