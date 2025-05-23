# import os
# import requests
# import hmac
# import hashlib
# import psycopg2
# import logging
# from datetime import datetime
# from tqdm import tqdm
# import sys
# import pandas as pd

# # Set up logging
# logging.basicConfig(filename='kyc_media_download.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# # Veriff API endpoints
# BASE_URL = "https://stationapi.veriff.com/v1"  # Removed trailing space
# SESSION_MEDIA_ENDPOINT = "/sessions/{sessionID}/media"
# MEDIA_ENDPOINT = "/media/{mediaID}"

# # Your Veriff credentials
# X_AUTH_CLIENT = "f0d83487-9b6a-4cb8-80cf-31098983aa1d"
# SHARED_SECRET_KEY = "cf4da2fc-a8eb-4c99-ab96-1f129a2a02fb"

# # PostgreSQL database credentials
# DB_HOST = "wearhouse.cmnbamv2oloq.ap-south-1.rds.amazonaws.com"
# DB_USER = "readonly"
# DB_PASSWORD = "readonly123"
# DB_DATABASE = "postgres"

# def save_media(media_item, email):
#     media_url = media_item['url']
#     media_id = media_url.rsplit('/', 1)[-1]
#     mimetype = media_item['mimetype']
#     file_extension = mimetype.split('/')[-1]

#     # Generate the X-HMAC-SIGNATURE using the mediaID and shared secret key
#     media_signature = hmac.new(
#         bytes(SHARED_SECRET_KEY, 'latin-1'),
#         msg=bytes(media_id, 'latin-1'),
#         digestmod=hashlib.sha256
#     ).hexdigest()

#     # Construct the full URL for individual media
#     media_url = BASE_URL + MEDIA_ENDPOINT.format(mediaID=media_id)

#     # Set up the headers for the media request
#     media_headers = {
#         "X-AUTH-CLIENT": X_AUTH_CLIENT,
#         "X-HMAC-SIGNATURE": media_signature
#     }

#     # Make the GET request to get the media
#     media_response = requests.get(media_url, headers=media_headers)
#     if media_response.status_code == 200:
#         # Save the media file to a folder named after the email inside the KYC directory
#         base_folder = "KYC"
#         folder_path = os.path.join(base_folder, email)

#         # Create the directory if it doesn't exist
#         if not os.path.exists(folder_path):
#             os.makedirs(folder_path)

#         file_path = os.path.join(folder_path, f"{media_id}.{file_extension}")
#         with open(file_path, 'wb') as file:
#             file.write(media_response.content)
#         return True
#     else:
#         logging.error(f"Failed to retrieve media for mediaID {media_id}. Status code: {media_response.status_code}, Response: {media_response.text}")
#         return False

# def get_media(session_id, email):
#     # Log the session ID being used
#     logging.info(f"Attempting to fetch media for email {email} with session ID {session_id}")

#     # Check if folder for the email already exists
#     base_folder = "KYC"
#     folder_path = os.path.join(base_folder, email)
#     if os.path.exists(folder_path):
#         logging.info(f"Folder for email {email} already exists. Skipping session.")
#         return False

#     # Construct the full URL for session media
#     session_url = BASE_URL + SESSION_MEDIA_ENDPOINT.format(sessionID=session_id)
#     logging.info(f"Constructed session URL: {session_url}")

#     session_signature = hmac.new(
#         bytes(SHARED_SECRET_KEY, 'latin-1'),
#         msg=bytes(session_id, 'latin-1'),
#         digestmod=hashlib.sha256
#     ).hexdigest()

#     # Set up the headers for the session media request
#     headers = {
#         "X-AUTH-CLIENT": X_AUTH_CLIENT,
#         "X-HMAC-SIGNATURE": session_signature
#     }

#     # Make the GET request to get media URLs
#     response = requests.get(session_url, headers=headers)
#     if response.status_code != 200:
#         logging.error(f"Failed to retrieve media URLs for email {email}. Status code: {response.status_code}, Response: {response.text}")
#         return False

#     media_data = response.json()
#     success = False
#     for media_type in ['images', 'videos']:
#         for media_item in media_data.get(media_type, []):
#             if save_media(media_item, email):
#                 success = True
#     return success

# def fetch_data_and_download_media():
#     # Connect to the PostgreSQL database
#     connection = psycopg2.connect(
#         host=DB_HOST,
#         user=DB_USER,
#         password=DB_PASSWORD,
#         database=DB_DATABASE
#     )
#     cursor = connection.cursor()

#     # Fetch emails from kyc table
#     query = """
#     SELECT email, platform_id, login 
#     FROM data_analytics.kyc 
#     WHERE platform_id NOT LIKE '%system%' 
#     AND user_agreement = 0 
#     AND platform_id LIKE '%-%'
#     AND email IN (
#     'ajaljaberi7318@gmail.com',
#     'cheungy2k@gmail.com',
#     'Habeebkola1@gmail.com',
#     'rap4you098@gmail.com',
#     'r.foreignexchange@outlook.com',
#     'mohdhassan2209@gmail.com',
#     'pedro.rodrigues14492@gmail.com',
#     'ivantang966@gmail.com',
#     'nivanmathew23@icloud.com',
#     'zualfqarjubouri@gmail.com',
#     'rlgmltd@gmail.com',
#     'paulosgate4@hotmail.com',
#     'trader.ezragamboa@gmail.com',
#     'ouaskouk7@gmail.com',
#     'bob_x5@hotmail.com',
#     'giancarloferrandino64@gmail.com',
#     'donnopierpaolo@gmail.com',
#     'thomas1212121212@outlook.es',
#     'mateusztyda89@gmail.com',
#      'hshafique580@gmail.com',
#     'naim.mahrek@gmail.com',
#     'sutucka@hotmail.com',
#     'fardusaahmed739@gmail.com',
#     'nellyyacoub86@gmail.com',
#     'monidama8@gmail.com',
#     'shaktikr934@gmail.com',
#     'Evolutionjcrs@gmail.com',
#     'lcprtrades@hotmail.com',
#     'josecamponovo@gmail.com',
#     'xr0tagxr0@gmail.com',
#     'aboraba043@gmail.com',
#     'Yaseenkhanjani777@gmail.com',
#     'ylakhnach59@gmail.com',
#     'kostasth13@icloud.com',
#     'Ramana.Kamarshi@gmail.com',
#     'dorleanb21@gmail.com'
#     )
#     ORDER BY created_at DESC;
#     """

#     cursor.execute(query)
#     records = cursor.fetchall()

#     if not records:
#         logging.info("No matching KYC records found for May 21, 2025.")
#         cursor.close()
#         connection.close()
#         return

#     total_emails = len(records)
#     success_count = 0
#     failed_emails = []
#     data = []

#     # Process each record
#     for record in tqdm(records, desc="Downloading media", ncols=100, file=sys.stdout):
#         email, veriff_id, login = record
#         video_verdict = " " if get_media(veriff_id, email) else "No Media Found"
#         data.append([email, login, video_verdict])
#         if video_verdict == "No Media Found":
#             failed_emails.append(email)
#         else:
#             success_count += 1

#     cursor.close()
#     connection.close()

#     # Export results to CSV
#     df = pd.DataFrame(data, columns=['email', 'login', 'Video Verdict'])
#     df.to_csv('KYC Video Verdict.csv', index=False)

#     # Print download summary
#     print(f"\n\nDownload Summary:")
#     print(f"Total emails processed: {total_emails}")
#     print(f"Successfully downloaded media for: {success_count} emails")
#     print(f"Failed to find media for: {len(failed_emails)} emails")

#     if failed_emails:
#         print("\nEmails with no media found:")
#         for email in failed_emails:
#             print(f"- {email}")

# # Execute the function to fetch data and download media
# fetch_data_and_download_media()



###########################################################################################################################################################################################

# import os
# import requests
# import hmac
# import hashlib
# import psycopg2
# import logging
# import pandas as pd
# from tqdm import tqdm
# import sys

# # Set up logging
# logging.basicConfig(filename='kyc_media_download.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# # Veriff API endpoints
# BASE_URL = "https://stationapi.veriff.com/v1"
# SESSION_MEDIA_ENDPOINT = "/sessions/{sessionID}/media"
# MEDIA_ENDPOINT = "/media/{mediaID}"

# # Your Veriff credentials
# X_AUTH_CLIENT = "f0d83487-9b6a-4cb8-80cf-31098983aa1d"
# SHARED_SECRET_KEY = "cf4da2fc-a8eb-4c99-ab96-1f129a2a02fb"

# # PostgreSQL database credentials
# DB_HOST = "wearhouse.cmnbamv2oloq.ap-south-1.rds.amazonaws.com"
# DB_USER = "readonly"
# DB_PASSWORD = "readonly123"
# DB_DATABASE = "postgres"

# def save_media(media_item, email):
#     media_url = media_item['url']
#     media_id = media_url.rsplit('/', 1)[-1]
#     mimetype = media_item['mimetype']
#     file_extension = mimetype.split('/')[-1]

#     media_signature = hmac.new(bytes(SHARED_SECRET_KEY, 'latin-1'), msg=bytes(media_id, 'latin-1'), digestmod=hashlib.sha256).hexdigest()
#     media_url = BASE_URL + MEDIA_ENDPOINT.format(mediaID=media_id)
#     media_headers = {
#         "X-AUTH-CLIENT": X_AUTH_CLIENT,
#         "X-HMAC-SIGNATURE": media_signature
#     }

#     media_response = requests.get(media_url, headers=media_headers)
#     if media_response.status_code == 200:
#         base_folder = "KYC"
#         folder_path = os.path.join(base_folder, email)
#         if not os.path.exists(folder_path):
#             os.makedirs(folder_path)
#         file_path = os.path.join(folder_path, f"{media_id}.{file_extension}")
#         with open(file_path, 'wb') as file:
#             file.write(media_response.content)
#         return True
#     else:
#         logging.error(f"Failed to retrieve media for mediaID {media_id}. Status code: {media_response.status_code}, Response: {media_response.text}")
#         return False

# def get_media(session_id, email):
#     base_folder = "KYC"
#     folder_path = os.path.join(base_folder, email)
#     if os.path.exists(folder_path):
#         logging.info(f"Folder for email {email} already exists. Skipping session.")
#         return False

#     session_url = BASE_URL + SESSION_MEDIA_ENDPOINT.format(sessionID=session_id)
#     session_signature = hmac.new(bytes(SHARED_SECRET_KEY, 'latin-1'), msg=bytes(session_id, 'latin-1'), digestmod=hashlib.sha256).hexdigest()
#     headers = {
#         "X-AUTH-CLIENT": X_AUTH_CLIENT,
#         "X-HMAC-SIGNATURE": session_signature
#     }

#     response = requests.get(session_url, headers=headers)
#     if response.status_code != 200:
#         logging.error(f"Failed to retrieve media URLs for email {email}. Status code: {response.status_code}, Response: {response.text}")
#         return False

#     media_data = response.json()
#     success = False
#     for media_type in ['images', 'videos']:
#         for media_item in media_data.get(media_type, []):
#             if save_media(media_item, email):
#                 success = True
#     return success

# def fetch_data_and_download_media():
#     # Connect to the PostgreSQL database
#     connection = psycopg2.connect(
#         host=DB_HOST,
#         user=DB_USER,
#         password=DB_PASSWORD,
#         database=DB_DATABASE
#     )

#     cursor = connection.cursor()
    
#     # Fetch emails from investigation_demo_v1
#     email_query = """
#     SELECT 
#         lower(email) as email
#     FROM data_analytics.investigation_demo_v1
# 	Where date(checking_date) BETWEEN '2025-03-21' AND '2025-04-30'
# 	and kyc_issue IN ('Yes', 'kyc_issue')
#     """
#     cursor.execute(email_query)
#     email_records = cursor.fetchall()
#     emails = [record[0] for record in email_records if record[0]]
    
#     if not emails:
#         logging.info("No emails found for the given date range and kyc_issue criteria.")
#         cursor.close()
#         connection.close()
#         return

#     # Fetch platform_id and login from kyc table in batches
#     batch_size = 50
#     kyc_records = []
#     for i in range(0, len(emails), batch_size):
#         batch = emails[i:i + batch_size]
#         in_clause = ', '.join(f"'{email}'" for email in batch)
#         kyc_query = f"""
#         SELECT email, platform_id, login
#         FROM data_analytics.kyc 
#         WHERE platform_id NOT LIKE '%system%' 
#             AND user_agreement = 0 
#             AND platform_id LIKE '%-%'
#             AND email IN ({in_clause})
#         ORDER BY updated_at DESC
#         """
        
#         logging.info(f"Executing query: {kyc_query}")
#         cursor.execute(kyc_query)
#         batch_records = cursor.fetchall()
#         kyc_records.extend(batch_records)

#     if not kyc_records:
#         logging.info("No matching records found in kyc table for the given emails.")
#         cursor.close()
#         connection.close()
#         return

#     # Download media and track results
#     total_emails = len(kyc_records)
#     success_count = 0
#     failed_emails = []
#     data = []

#     for record in tqdm(kyc_records, desc="Downloading media", ncols=100, file=sys.stdout):
#         email, veriff_id, login = record
#         video_verdict = " " if get_media(veriff_id, email) else "No Media Found"
#         data.append([email, login, video_verdict])
#         if video_verdict == "No Media Found":
#             failed_emails.append(email)
#         else:
#             success_count += 1

#     cursor.close()
#     connection.close()

#     # Create DataFrame
#     df = pd.DataFrame(data, columns=['email', 'login', 'Video Verdict'])
    
#     # Save DataFrame to CSV
#     df.to_csv('KYC Video Verdict.csv', index=False)

#     # Print download summary
#     print(f"\n\nDownload Summary:")
#     print(f"Total emails processed: {total_emails}")
#     print(f"Successfully downloaded media for: {success_count} emails")
#     print(f"Failed to find media for: {len(failed_emails)} emails")
    
#     if failed_emails:
#         print("\nEmails with no media found:")
#         for email in failed_emails:
#             print(f"- {email}")

# # Execute the function to fetch data and download media
# fetch_data_and_download_media()