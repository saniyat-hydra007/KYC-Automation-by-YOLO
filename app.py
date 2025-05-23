from flask import Flask, render_template, request
import pandas as pd
import os
import sys
import importlib.util
import logging
import webbrowser
import threading

# def open_browser():
#     webbrowser.open_new("http://127.0.0.1:5000")
    
app = Flask(__name__)

# Paths for CSV and folders
BASE_DIR = r"D:\Saniyat\Saniyat_s CODE\KYC Automation FLASK"
CSV_PATH = os.path.join(BASE_DIR, "KYC Video Verdict.csv")

# Set up logging
logging.basicConfig(filename=os.path.join(BASE_DIR, 'app_execution.log'), level=logging.INFO, format='%(asctime)s - %(message)s')

def run_script(script_name):
    """Helper function to dynamically run a Python script."""
    logging.info(f"Running {script_name}")
    try:
        script_path = os.path.join(BASE_DIR, script_name)
        if not os.path.exists(script_path):
            logging.error(f"Script {script_name} not found at {script_path}")
            return False, f"Script {script_name} not found"

        # Dynamically import and run the script
        spec = importlib.util.spec_from_file_location(script_name, script_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[script_name] = module
        spec.loader.exec_module(module)
        logging.info(f"Successfully executed {script_name}")
        return True, f"Successfully executed {script_name}"
    except Exception as e:
        logging.error(f"Error executing {script_name}: {str(e)}")
        return False, f"Error executing {script_name}: {str(e)}"

@app.route('/')
def index():
    # Check for skip parameter to avoid running scripts
    skip_run = request.args.get('skip', 'false').lower() == 'true'

    # List of scripts to run in order
    scripts = [
        'auto_media_extract.py',
        'yolo_first_pass.py',
        'Delete_annotated.py',
        'yolo_second_pass.py',
        'yolo_third_pass.py',
        'save_To.py',
        'validation.py',
        'yolo_hand_feet copy.py'
    ]
    
    # Run scripts unless explicitly skipped
    script_results = []
    if not skip_run:
        logging.info("Starting script execution")
        for script in scripts:
            script_results.append({'script': script, 'success': None, 'message': f"Running {script}"})
            success, message = run_script(script)
            script_results[-1] = {'script': script, 'success': success, 'message': message}
    else:
        script_results = [{'script': script, 'success': True, 'message': f"{script} skipped (skip parameter enabled)"} for script in scripts]

    # Load the final CSV
    data = []
    error = None
    try:
        if os.path.exists(CSV_PATH):
            df = pd.read_csv(CSV_PATH)
            logging.info(f"Loaded CSV: {CSV_PATH}, rows: {len(df)}")
            if df.empty or df.dropna().empty:
                error = "CSV file is empty or contains only headers"
                logging.warning("CSV file is empty or contains only headers")
            elif not all(col in df.columns for col in ['email', 'Video Verdict']):
                error = "CSV missing required columns (email, Video Verdict)"
                logging.warning("CSV missing required columns")
            else:
                # Filter out invalid email entries
                df = df[df['email'].str.contains('@', na=False)]
                data = df.to_dict('records')
        else:
            error = "Final CSV file not found"
            logging.warning("Final CSV file not found")
    except Exception as e:
        error = f"Error loading CSV: {str(e)}"
        logging.error(f"Error loading CSV: {str(e)}")

    return render_template('index.html', data=data, script_results=script_results, error=error)

if __name__ == '__main__':
    # Start the browser a little after the server starts
    # threading.Timer(1.25, open_browser).start()
    app.run(debug=True)