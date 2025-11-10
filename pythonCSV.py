from models import Athlete, RPEEntry, get_session, get_engine
from sqlalchemy import func
import pandas as pd

def get_data_from_db(db_path='data/rpe_tracker.db'):
    """Load data from database instead of CSV"""
    session = get_session(get_engine(db_path))
    
    try:
        # Query all data
        query = session.query(
            Athlete.id,
            Athlete.email,
            Athlete.first_name,
            Athlete.last_name,
            Athlete.position,
            Athlete.summer_attendance,
            RPEEntry.date,
            RPEEntry.rpe_value.label('value')
        ).join(RPEEntry, Athlete.id == RPEEntry.athlete_id, isouter=True)
        
        df_long = pd.read_sql(query.statement, session.bind)
        
        # If no RPE data yet, return athlete info only
        if df_long.empty or df_long['date'].isna().all():
            athletes = session.query(Athlete).all()
            empty_df = pd.DataFrame([{
                'Email': a.email,
                'First Name': a.first_name,
                'Last Name': a.last_name,
                'Position': a.position,
                'Summer Attendance': a.summer_attendance,
                'Name': f"{a.first_name} {a.last_name}",
                'Average Value': 0
            } for a in athletes])
            empty_long = pd.DataFrame(columns=['Position', 'Name', 'Email', 'Date', 'Value'])
            empty_pos = pd.DataFrame(columns=['Position', 'Date', 'Value'])
            return empty_df, empty_long, empty_pos
        
        # Format data
        df_long['Email'] = df_long['email'].str.strip().str.lower()
        df_long['Name'] = df_long['first_name'] + ' ' + df_long['last_name']
        df_long['Date'] = pd.to_datetime(df_long['date'])
        df_long['Value'] = pd.to_numeric(df_long['value'], errors='coerce')
        df_long = df_long[['Position', 'Name', 'Email', 'Date', 'Value']].copy()
        
        # Create wide format
        df_wide = df_long.pivot_table(
            index=['Email', 'Name', 'Position'],
            columns='Date',
            values='Value',
            aggfunc='first'
        ).reset_index()
        
        # Calculate averages
        date_columns = [col for col in df_wide.columns if isinstance(col, pd.Timestamp)]
        df_wide['Average Value'] = df_wide[date_columns].mean(axis=1)
        
        # Position averages
        df_position_daily_avg = df_long.groupby(['Position', 'Date'])['Value'].mean().reset_index()
        
        return df_wide, df_long, df_position_daily_avg
        
    finally:
        session.close()

def get_data_from_csv():
    """Now uses database instead of CSV"""
    return get_data_from_db()

