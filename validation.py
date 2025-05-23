import pandas as pd
import psycopg2
from psycopg2 import Error

# Database connection parameters
db_params = {
    "dbname": "postgres",
    "user": "readonly",
    "password": "readonly123",
    "host": "wearhouse.cmnbamv2oloq.ap-south-1.rds.amazonaws.com",
    "port": "5432"
}

# Paths
kyc_csv_path = r"D:\Saniyat\Saniyat_s CODE\KYC Automation TEST\KYC Video Verdict.csv"
output_csv_path = r"D:\Saniyat\Saniyat_s CODE\KYC Automation TEST\validation_result.csv"

# Load the existing KYC Video Verdict CSV
try:
    kyc_df = pd.read_csv(kyc_csv_path)
except Exception as e:
    print(f"Error reading KYC Video Verdict.csv: {e}")
    exit()

# Filter out rows with 'No Media Found'
kyc_df = kyc_df[kyc_df['Video Verdict'] != 'No Media Found']

# Get unique emails for the SQL query
emails = tuple(kyc_df['email'].unique())
if len(emails) == 1:
    emails = f"('{emails[0]}')"  # Handle single email case
else:
    emails = str(emails)  # Convert tuple to string for IN clause

# SQL query with parameterized emails
sql_query = f"""
SELECT 
    lower(email) AS email,
    kyc_issue
FROM data_analytics.investigation_demo_v1
WHERE email IN {emails}
"""

# Connect to PostgreSQL and fetch data
try:
    connection = psycopg2.connect(**db_params)
    cursor = connection.cursor()
    cursor.execute(sql_query)
    db_data = cursor.fetchall()
    cursor.close()
    connection.close()

    # Convert database data to DataFrame
    db_df = pd.DataFrame(db_data, columns=['email', 'kyc_issue'])

    # Merge KYC DataFrame with database DataFrame
    merged_df = pd.merge(kyc_df, db_df, on='email', how='left')

    # Function to determine the Mark
    def get_mark(row):
        if pd.isna(row['kyc_issue']):
            return "N/A"  # No data in database
        verdict = row['Video Verdict'].lower()
        issue = row['kyc_issue'].lower()
        if (verdict == 'flagged' and issue == 'yes') or (verdict == 'clean' and issue == 'no'):
            return "-/ (tick)"
        else:
            return "X (cross)"

    # Apply the Mark function
    merged_df['Mark'] = merged_df.apply(get_mark, axis=1)

    # Select and reorder columns
    validation_df = merged_df[['email', 'login', 'Video Verdict', 'kyc_issue', 'Mark']]

    # Save to new CSV
    validation_df.to_csv(output_csv_path, index=False)
    print(f"Validation result saved to {output_csv_path}")
    print(validation_df)

except Error as e:
    print(f"Database error: {e}")
    exit()