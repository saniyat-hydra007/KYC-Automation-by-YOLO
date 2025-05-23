import pandas as pd

# Paths to input and output CSV files
evidence_status_csv = "evidence_status_updated_version.csv"
kyc_verdict_csv = "KYC Video Verdict.csv"
output_csv = "KYC Video Verdict.csv"

# Read the CSV files
evidence_df = pd.read_csv(evidence_status_csv)
kyc_df = pd.read_csv(kyc_verdict_csv)

# Function to get status from evidence_status_updated_hand_feet.csv for a given email
def get_status(email, evidence_df):
    # Filter rows in evidence_df for the given email
    matching_rows = evidence_df[evidence_df['email'] == email]
    if not matching_rows.empty:
        # Return the first status found (in case of duplicates)
        return matching_rows['Video Verdict'].iloc[0]
    return None

# Update the Video Verdict column
kyc_df['Video Verdict'] = kyc_df.apply(
    lambda row: row['Video Verdict'] if pd.notna(row['Video Verdict']) and row['Video Verdict'] == "No Media Found"
    else get_status(row['email'], evidence_df) if get_status(row['email'], evidence_df) is not None
    else row['Video Verdict'] if pd.notna(row['Video Verdict']) else "",
    axis=1
)

# Save the updated DataFrame to a new CSV
kyc_df.to_csv(output_csv, index=False)
print(f"Updated KYC Video Verdict saved to {output_csv}")
print(kyc_df)