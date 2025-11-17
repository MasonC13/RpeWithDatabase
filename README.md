# Truman State University RPE Tracker - Database Migration

This repository contains the migration scripts to convert the original CSV-based RPE tracking system to a normalized SQLite database using SQLAlchemy ORM.

---

## 🔄 Migration Overview

The original RPE Tracker stored all data in CSV files with dates as column headers. This approach has been replaced with a normalized SQLite database for better performance, data integrity, and scalability.

---

## 📄 Migration Files

### `migrate_csv_to_sqlite.py`
The primary migration script that converts existing CSV data to SQLite.

**What it does:**
- Reads `responses.csv`, `caffeine.csv`, and `sleep.csv` (if they exist)
- Creates a normalized SQLite database at `data/rpe_tracker.db`
- Migrates athlete information to the `athletes` table
- Converts date columns (e.g., "06/15/2024") into individual entries in `rpe_entries`, `caffeine_entries`, or `sleep_entries` tables
- Handles duplicate entries (updates existing records instead of creating duplicates)
- Manages various CSV encodings (UTF-8, Latin-1, CP1252)
- Validates data during migration (skips invalid emails, unparseable dates, non-numeric values)
- Provides detailed migration statistics and verification

**Usage:**
```bash
python migrate_csv_to_sqlite.py
```

**Output:**
- Creates `data/rpe_tracker.db`
- Displays migration progress and statistics
- Shows sample data verification
- Reports total athletes, entries, date ranges, and position distribution

---

### `load_csv_to_mysql.py`
Alternative migration script (nearly identical to `migrate_csv_to_sqlite.py`).

**Key Differences:**
- Slightly different handling of NaN values using `pd.notna()` checks
- Same core functionality as `migrate_csv_to_sqlite.py`
- Despite the filename mentioning MySQL, it creates SQLite databases

**Note:** Both scripts produce the same result. Use `migrate_csv_to_sqlite.py` as the primary migration tool.

---

## 🗄️ Database Schema

The migration creates a normalized relational database with the following structure:

**athletes**
- One row per athlete
- Stores: email (unique), name, position, attendance info
- Primary key: `id`

**rpe_entries**
- One row per athlete per date
- Stores: `athlete_id`, `date`, `rpe_value`
- Foreign key relationship to athletes

**caffeine_entries** (if caffeine.csv exists)
- One row per athlete per date
- Stores: `athlete_id`, `date`, `caffeine_mg`

**sleep_entries** (if sleep.csv exists)
- One row per athlete per date
- Stores: `athlete_id`, `date`, `sleep_hours`

---

## 🔍 Migration Process

### Before Migration (CSV Format)
```
Email, Last Name, First Name, Position, 06/01/2024, 06/02/2024, 06/03/2024
athlete@example.com, Smith, John, Forward, 7, 8, 6
```

### After Migration (SQLite Database)

**athletes table:**
```
id | email                  | last_name | first_name | position
1  | athlete@example.com    | Smith     | John       | Forward
```

**rpe_entries table:**
```
id | athlete_id | date       | rpe_value
1  | 1          | 2024-06-01 | 7
2  | 1          | 2024-06-02 | 8
3  | 1          | 2024-06-03 | 6
```

---

## ⚙️ Migration Features

### Data Validation
- Skips rows with missing or invalid emails
- Handles NaN values gracefully
- Converts values to appropriate types (float for RPE, string for names)
- Parses dates from column headers automatically

### Error Handling
- Multiple CSV encoding support (UTF-8, Latin-1, CP1252)
- Rollback on errors to prevent partial migrations
- Detailed error messages with stack traces
- Continues processing valid data when individual entries fail

### Smart Updates
- Checks for existing athletes and entries before inserting
- Updates existing records instead of creating duplicates
- Maintains data integrity with foreign key constraints

### Verification
- Displays sample athletes and entries after migration
- Shows date range of RPE data
- Reports athlete distribution by position
- Provides total counts for all tables

---

## 📊 Migration Statistics Example

```
==========================================================
CSV TO SQLITE MIGRATION SCRIPT
Truman State University RPE Tracker
==========================================================

Reading responses.csv...
Found 45 rows in CSV
Found 120 date columns

--- Migrating Athletes ---
Athletes migrated: 45 new, 0 updated

--- Migrating RPE Entries ---
Entries migrated: 4800, skipped: 120

--- Migration Summary ---
Total athletes in database: 45
Total rpe entries in database: 4800

✅ Migration complete! Database saved to data/rpe_tracker.db

==========================================================
VERIFYING MIGRATION
==========================================================

Sample Athletes (45 total):
  John Smith (athlete@example.com) - Forward
  ...

Date range: 2024-06-01 to 2024-10-15

Athletes by position:
  Forward: 15
  Midfielder: 12
  Defender: 10
  Goalkeeper: 8
```

---

## 🚨 Important Notes

1. **Backup your CSV files** - Keep original CSV files as backup before running migration
2. **Run once** - The migration is idempotent but should only need to run once
3. **Check verification output** - Review the sample data to ensure migration succeeded
4. **Update Flask app** - Modify your Flask application to use SQLAlchemy queries instead of CSV operations
5. **Database location** - The SQLite file is created at `data/rpe_tracker.db`

---

## 🔗 Integration with Original Project

After running the migration, update your Flask application (`main.py`) to:
- Import and use the SQLAlchemy models from `models.py`
- Replace pandas CSV operations with SQLAlchemy queries
- Use database sessions instead of direct CSV file access

The original React frontend and dashboard functionality remain unchanged - only the backend data layer is updated.

---

## 📝 Next Steps After Migration

1. Test database operations: `python db_operations.py`
2. Update Flask routes to use SQLAlchemy
3. Verify dashboard still displays data correctly
4. Archive original CSV files
5. Update deployment documentation
