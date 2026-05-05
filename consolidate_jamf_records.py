#!/usr/bin/env python3
"""
iPad Fleet Data Consolidation Script
Consolidates multiple CSV exports into a master database with user history tracking
"""

import pandas as pd
import glob
import os
from datetime import datetime
from pathlib import Path


def consolidate_ipad_data(input_folder, output_folder=None):
    """
    Consolidate all CSV files from input_folder into master files

    Args:
        input_folder: Path to folder containing CSV files
        output_folder: Path to save output files (defaults to input_folder)
    """

    if output_folder is None:
        output_folder = input_folder

    # Create output folder if it doesn't exist
    Path(output_folder).mkdir(parents=True, exist_ok=True)

    # Find all CSV files
    csv_files = glob.glob(os.path.join(input_folder, "*.csv"))

    if not csv_files:
        print(f"❌ No CSV files found in {input_folder}")
        return

    print(f"📁 Found {len(csv_files)} CSV files")
    print("=" * 60)

    # Store all records for processing
    all_records = []
    files_processed = 0
    files_with_errors = []

    # Read all CSV files
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file, encoding='utf-8')

            # Skip if no Serial Number column
            if 'Serial Number' not in df.columns:
                print(f"⚠️  Skipping {os.path.basename(csv_file)} - no Serial Number column")
                continue

            # Add source file column for tracking
            df['Source_File'] = os.path.basename(csv_file)

            # Remove completely empty rows
            df = df.dropna(how='all')

            all_records.append(df)
            files_processed += 1
            print(f"✅ Processed: {os.path.basename(csv_file)} ({len(df)} records)")

        except Exception as e:
            files_with_errors.append((csv_file, str(e)))
            print(f"❌ Error reading {os.path.basename(csv_file)}: {e}")

    if not all_records:
        print("\n❌ No valid data found to consolidate")
        return

    print("\n" + "=" * 60)
    print(f"✅ Successfully processed {files_processed} files")

    if files_with_errors:
        print(f"⚠️  {len(files_with_errors)} files had errors")

    # Combine all dataframes
    print("\n🔄 Combining all records...")
    combined_df = pd.concat(all_records, ignore_index=True, sort=False)

    # Remove rows with empty serial numbers
    combined_df = combined_df[combined_df['Serial Number'].notna()]
    combined_df = combined_df[combined_df['Serial Number'].str.strip() != '']

    print(f"📊 Total records: {len(combined_df)}")
    print(f"📊 Unique serial numbers: {combined_df['Serial Number'].nunique()}")

    # Identify user identifier columns (try multiple possibilities)
    user_id_columns = []
    for col in ['Username', 'Display Name', 'Email Address']:
        if col in combined_df.columns:
            user_id_columns.append(col)

    # Identify date columns for sorting
    date_columns = [col for col in combined_df.columns if
                    any(date_word in col.lower() for date_word in
                        ['date', 'update', 'backup', 'inventory', 'expiration'])]

    # Convert date columns to datetime for proper sorting
    for col in date_columns:
        try:
            combined_df[col] = pd.to_datetime(combined_df[col], errors='coerce')
        except:
            pass

    # Sort by serial number and most recent date (if available)
    if date_columns:
        # Use Last Inventory Update if available, otherwise first date column
        sort_col = 'Last Inventory Update' if 'Last Inventory Update' in date_columns else date_columns[0]
        combined_df = combined_df.sort_values(['Serial Number', sort_col],
                                              ascending=[True, False],
                                              na_position='last')
    else:
        combined_df = combined_df.sort_values('Serial Number')

    # === OUTPUT 1: Complete Raw Data ===
    raw_output = os.path.join(output_folder, f"iPad_Fleet_Raw_Data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    combined_df.to_csv(raw_output, index=False)
    print(f"\n✅ Raw data saved: {raw_output}")

    # === OUTPUT 2: Master Device List (one row per device, most recent data) ===
    print("\n🔄 Creating master device list...")

    # For each serial number, keep the most recent record
    master_df = combined_df.groupby('Serial Number').first().reset_index()

    # Count assignments per device
    assignment_counts = combined_df.groupby('Serial Number').size().reset_index(name='Total_Assignments')
    master_df = master_df.merge(assignment_counts, on='Serial Number', how='left')

    master_output = os.path.join(output_folder, f"iPad_Fleet_Master_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    master_df.to_csv(master_output, index=False)
    print(f"✅ Master device list saved: {master_output}")
    print(f"   📊 {len(master_df)} unique devices")

    # === OUTPUT 3: User Assignment History ===
    print("\n🔄 Creating user assignment history...")

    # Create history records with relevant user/assignment info
    history_columns = ['Serial Number'] + user_id_columns + ['Full Name'] + date_columns + ['Source_File']
    history_columns = [col for col in history_columns if col in combined_df.columns]

    history_df = combined_df[history_columns].copy()

    # Remove duplicate assignments (same user, same device, same date)
    history_df = history_df.drop_duplicates()

    # Sort by serial number and date
    if date_columns:
        history_df = history_df.sort_values(['Serial Number', sort_col],
                                            ascending=[True, False],
                                            na_position='last')

    history_output = os.path.join(output_folder,
                                  f"iPad_Fleet_User_History_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    history_df.to_csv(history_output, index=False)
    print(f"✅ User assignment history saved: {history_output}")
    print(f"   📊 {len(history_df)} assignment records")

    # === OUTPUT 4: Devices with Multiple Users ===
    print("\n🔄 Identifying devices with multiple users...")

    multi_user_serials = assignment_counts[assignment_counts['Total_Assignments'] > 1]['Serial Number']
    multi_user_df = history_df[history_df['Serial Number'].isin(multi_user_serials)]

    if len(multi_user_df) > 0:
        multi_user_output = os.path.join(output_folder,
                                         f"iPad_Fleet_Multiple_Users_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        multi_user_df.to_csv(multi_user_output, index=False)
        print(f"✅ Multiple user assignments saved: {multi_user_output}")
        print(f"   📊 {len(multi_user_serials)} devices with multiple users")
        print(f"   📊 {len(multi_user_df)} total assignment records for these devices")
    else:
        print("ℹ️  No devices found with multiple user assignments")

    # === SUMMARY STATISTICS ===
    print("\n" + "=" * 60)
    print("📊 CONSOLIDATION SUMMARY")
    print("=" * 60)
    print(f"Files processed: {files_processed}")
    print(f"Total records: {len(combined_df)}")
    print(f"Unique devices: {len(master_df)}")
    print(f"Devices with multiple users: {len(multi_user_serials)}")
    print(f"Total assignment records: {len(history_df)}")

    # Show column coverage
    print(f"\nTotal unique columns across all files: {len(combined_df.columns)}")
    print("\nMost common columns:")
    non_null_counts = combined_df.count().sort_values(ascending=False).head(10)
    for col, count in non_null_counts.items():
        pct = (count / len(combined_df)) * 100
        print(f"  • {col}: {count} records ({pct:.1f}%)")

    print("\n" + "=" * 60)
    print("✅ CONSOLIDATION COMPLETE!")
    print("=" * 60)


if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("iPad Fleet Data Consolidation Script")
    print("=" * 60)
    print()

    # Get input folder from command line or prompt user
    if len(sys.argv) > 1:
        input_folder = sys.argv[1]
    else:
        input_folder = input("Enter the path to your folder containing CSV files: ").strip()
        # Remove quotes if user pasted path with quotes
        input_folder = input_folder.strip('"').strip("'")

    # Get output folder (optional)
    if len(sys.argv) > 2:
        output_folder = sys.argv[2]
    else:
        output_folder = input("Enter output folder path (press Enter to use same folder): ").strip()
        output_folder = output_folder.strip('"').strip("'")
        if not output_folder:
            output_folder = None

    # Validate input folder exists
    if not os.path.exists(input_folder):
        print(f"\n❌ Error: Folder '{input_folder}' does not exist")
        sys.exit(1)

    if not os.path.isdir(input_folder):
        print(f"\n❌ Error: '{input_folder}' is not a folder")
        sys.exit(1)

    print()
    consolidate_ipad_data(input_folder, output_folder)