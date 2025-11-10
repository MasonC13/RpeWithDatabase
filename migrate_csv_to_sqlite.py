"""
Migration Script: CSV to SQLite
Converts responses.csv to normalized SQLite database using SQLAlchemy

This script:
1. Reads the existing CSV file(s)
2. Creates the SQLite database
3. Migrates athlete data to the athletes table
4. Migrates RPE data from date columns to rpe_entries table
5. Handles caffeine.csv and sleep.csv if they exist
"""

import pandas as pd
from datetime import datetime
from pathlib import Path
import sys
from models import Base, Athlete, RPEEntry, CaffeineEntry, SleepEntry, get_engine, get_session, init_db

# Base columns in the CSV that represent athlete info
BASE_COLUMNS = [
    "Email",
    "Last 4 Digits",
    "Last Name",
    "First Name",
    "Position",
    "Summer Attendance"
]

def migrate_csv_to_db(csv_file='responses.csv', db_path='data/rpe_tracker.db', data_type='rpe'):
    """
    Migrate CSV data to SQLite database
    
    Parameters:
    -----------
    csv_file : str
        Path to the CSV file
    db_path : str
        Path where the SQLite database will be created
    data_type : str
        Type of data: 'rpe', 'caffeine', or 'sleep'
    """
    
    # Ensure data directory exists
    Path('data').mkdir(exist_ok=True)
    
    # Initialize database (creates tables)
    print(f"Initializing database at {db_path}...")
    engine = init_db(db_path)
    session = get_session(engine)
    
    try:
        # Read CSV file
        print(f"\nReading {csv_file}...")
        if not Path(csv_file).exists():
            print(f"Warning: {csv_file} not found. Skipping.")
            return
        
        # Try different encodings
        try:
            df = pd.read_csv(csv_file, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(csv_file, encoding='latin-1')
                print("Note: Using latin-1 encoding due to special characters")
            except UnicodeDecodeError:
                df = pd.read_csv(csv_file, encoding='cp1252')
                print("Note: Using cp1252 encoding due to special characters")
        
        df.columns = df.columns.str.strip()  # Clean column names
        
        print(f"Found {len(df)} rows in CSV")
        print(f"Columns: {df.columns.tolist()}")
        
        # Clean email addresses
        if 'Email' in df.columns:
            df['Email'] = df['Email'].str.strip().str.lower()
        
        # Identify date columns (columns not in BASE_COLUMNS)
        date_columns = [col for col in df.columns if col not in BASE_COLUMNS]
        print(f"\nFound {len(date_columns)} date columns: {date_columns[:5]}..." if len(date_columns) > 5 else f"\nFound {len(date_columns)} date columns: {date_columns}")
        
        # Step 1: Migrate Athletes
        print("\n--- Migrating Athletes ---")
        athletes_migrated = 0
        athletes_updated = 0
        
        for idx, row in df.iterrows():
            email = row.get('Email', '')
            
            # Handle NaN or empty emails
            if pd.isna(email) or email == '':
                print(f"Skipping row {idx}: No email address")
                continue
            
            # Convert to string and clean
            email = str(email).strip().lower()
            
            if not email or email == 'nan':
                print(f"Skipping row {idx}: Invalid email")
                continue
            
            # Check if athlete already exists
            existing_athlete = session.query(Athlete).filter_by(email=email).first()
            
            if existing_athlete:
                # Update existing athlete info
                existing_athlete.last_4_digits = str(row.get('Last 4 Digits', '')) if pd.notna(row.get('Last 4 Digits')) else ''
                existing_athlete.last_name = str(row.get('Last Name', '')) if pd.notna(row.get('Last Name')) else ''
                existing_athlete.first_name = str(row.get('First Name', '')) if pd.notna(row.get('First Name')) else ''
                existing_athlete.position = str(row.get('Position', '')) if pd.notna(row.get('Position')) else ''
                existing_athlete.summer_attendance = str(row.get('Summer Attendance', '')) if pd.notna(row.get('Summer Attendance')) else ''
                existing_athlete.updated_at = datetime.utcnow()
                athletes_updated += 1
            else:
                # Create new athlete
                athlete = Athlete(
                    email=email,
                    last_4_digits=str(row.get('Last 4 Digits', '')) if pd.notna(row.get('Last 4 Digits')) else '',
                    last_name=str(row.get('Last Name', '')) if pd.notna(row.get('Last Name')) else '',
                    first_name=str(row.get('First Name', '')) if pd.notna(row.get('First Name')) else '',
                    position=str(row.get('Position', '')) if pd.notna(row.get('Position')) else '',
                    summer_attendance=str(row.get('Summer Attendance', '')) if pd.notna(row.get('Summer Attendance')) else ''
                )
                session.add(athlete)
                athletes_migrated += 1
        
        # Commit athlete changes
        session.commit()
        print(f"Athletes migrated: {athletes_migrated} new, {athletes_updated} updated")
        
        # Step 2: Migrate RPE/Caffeine/Sleep Entries from date columns
        if data_type == 'rpe':
            entry_class = RPEEntry
            value_field = 'rpe_value'
            print("\n--- Migrating RPE Entries ---")
        elif data_type == 'caffeine':
            entry_class = CaffeineEntry
            value_field = 'caffeine_mg'
            print("\n--- Migrating Caffeine Entries ---")
        elif data_type == 'sleep':
            entry_class = SleepEntry
            value_field = 'sleep_hours'
            print("\n--- Migrating Sleep Entries ---")
        else:
            print(f"Unknown data type: {data_type}")
            return
        
        entries_migrated = 0
        entries_skipped = 0
        
        for idx, row in df.iterrows():
            email = row.get('Email', '')
            
            # Handle NaN or empty emails
            if pd.isna(email) or email == '':
                continue
            
            email = str(email).strip().lower()
            
            if not email or email == 'nan':
                continue
            
            # Get athlete from database
            athlete = session.query(Athlete).filter_by(email=email).first()
            if not athlete:
                print(f"Warning: Athlete with email {email} not found in database")
                continue
            
            # Process each date column
            for date_col in date_columns:
                value = row.get(date_col)
                
                # Skip empty values
                if pd.isna(value) or value == '' or value == ' ':
                    continue
                
                try:
                    # Convert value to float
                    numeric_value = float(value)
                    
                    # Parse date from column name (format: MM/DD/YYYY)
                    date_obj = pd.to_datetime(date_col, errors='coerce')
                    if pd.isna(date_obj):
                        print(f"Warning: Could not parse date from column '{date_col}'")
                        entries_skipped += 1
                        continue
                    
                    # Check if entry already exists
                    existing_entry = session.query(entry_class).filter_by(
                        athlete_id=athlete.id,
                        date=date_obj.date()
                    ).first()
                    
                    if existing_entry:
                        # Update existing entry
                        setattr(existing_entry, value_field, numeric_value)
                    else:
                        # Create new entry
                        entry_data = {
                            'athlete_id': athlete.id,
                            'date': date_obj.date(),
                            value_field: numeric_value
                        }
                        entry = entry_class(**entry_data)
                        session.add(entry)
                        entries_migrated += 1
                
                except (ValueError, TypeError) as e:
                    entries_skipped += 1
                    continue
        
        # Commit all entries
        session.commit()
        print(f"Entries migrated: {entries_migrated}, skipped: {entries_skipped}")
        
        # Print summary statistics
        print("\n--- Migration Summary ---")
        total_athletes = session.query(Athlete).count()
        total_entries = session.query(entry_class).count()
        print(f"Total athletes in database: {total_athletes}")
        print(f"Total {data_type} entries in database: {total_entries}")
        
        print(f"\n✅ Migration complete! Database saved to {db_path}")
        
    except Exception as e:
        print(f"\n❌ Error during migration: {str(e)}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()


def verify_migration(db_path='data/rpe_tracker.db'):
    """
    Verify the migration by displaying sample data
    """
    print("\n" + "="*60)
    print("VERIFYING MIGRATION")
    print("="*60)
    
    engine = get_engine(db_path)
    session = get_session(engine)
    
    try:
        # Check athletes
        athletes = session.query(Athlete).limit(5).all()
        print(f"\nSample Athletes ({session.query(Athlete).count()} total):")
        for athlete in athletes:
            print(f"  {athlete.full_name} ({athlete.email}) - {athlete.position}")
        
        # Check RPE entries
        rpe_entries = session.query(RPEEntry).limit(5).all()
        print(f"\nSample RPE Entries ({session.query(RPEEntry).count()} total):")
        for entry in rpe_entries:
            athlete = entry.athlete
            print(f"  {athlete.full_name} - {entry.date}: RPE {entry.rpe_value}")
        
        # Check date range
        from sqlalchemy import func
        min_date = session.query(func.min(RPEEntry.date)).scalar()
        max_date = session.query(func.max(RPEEntry.date)).scalar()
        print(f"\nDate range: {min_date} to {max_date}")
        
        # Check positions
        positions = session.query(Athlete.position, func.count(Athlete.id)).group_by(Athlete.position).all()
        print(f"\nAthletes by position:")
        for position, count in positions:
            print(f"  {position}: {count}")
        
    finally:
        session.close()


if __name__ == '__main__':
    print("="*60)
    print("CSV TO SQLITE MIGRATION SCRIPT")
    print("Truman State University RPE Tracker")
    print("="*60)
    
    # Migrate RPE data (main file)
    migrate_csv_to_db(
        csv_file='responses.csv',
        db_path='data/rpe_tracker.db',
        data_type='rpe'
    )
    
    # Migrate caffeine data if file exists
    if Path('caffeine.csv').exists():
        print("\n" + "="*60)
        migrate_csv_to_db(
            csv_file='caffeine.csv',
            db_path='data/rpe_tracker.db',
            data_type='caffeine'
        )
    
    # Migrate sleep data if file exists
    if Path('sleep.csv').exists():
        print("\n" + "="*60)
        migrate_csv_to_db(
            csv_file='sleep.csv',
            db_path='data/rpe_tracker.db',
            data_type='sleep'
        )
    
    # Verify migration
    verify_migration()
    
    print("\n" + "="*60)
    print("MIGRATION COMPLETE!")
    print("Next steps:")
    print("1. Test the database with: python db_operations.py")
    print("2. Update your Flask app to use the new database")
    print("3. Keep your CSV files as backup")
    print("="*60)