import pandas as pd
from db import get_db
from io import StringIO
from fastapi import Depends
from datetime import timedelta
from datetime import datetime
from sqlalchemy import select, union
from model import Menu_hours, Store_status, Timezone,Report
from zoneinfo import ZoneInfo
from fastapi.responses import StreamingResponse
import csv
import io

def store_csv_to_db(csv_file_path, table_name, db=Depends(get_db)):
    df = pd.read_csv(csv_file_path,index_col=False)
    if 'timestamp_utc' in df.columns:
        df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'], errors='coerce', utc=True)
        
    

    buffer = StringIO()
    df.to_csv(buffer, index=False,header=False)
    buffer.seek(0)
    
    try:
        connection = db.connection().connection
        cursor = connection.cursor()
        if table_name == "timezones":
            cursor.copy_from(buffer, table_name, sep=',', null='', columns=('store_id', 'timezone_str'))
        elif table_name == "menu_hours":
            cursor.copy_from(buffer, table_name, sep=',', null='', columns=('store_id', 'dayOfWeek', 'start_time_local', 'end_time_local'))
        elif table_name == "store_status":
            cursor.copy_from(buffer, table_name, sep=',', null='', columns=('store_id', 'status', 'timestamp_utc'))
        connection.commit()
        cursor.close()
        print(f"CSV data successfully stored in {table_name} table.")
    except Exception as e:
       connection.rollback()
       cursor.close()
       print(f"Error storing CSV to DB: {e}")


       

def get_business_hour_interval(store_id, day_of_week, db=Depends(get_db)):
    res= db.query(Menu_hours).filter(
        Menu_hours.store_id == store_id,
        Menu_hours.dayOfWeek == day_of_week
    ).all()
    
    return [(x.start_time_local, x.end_time_local) for x in res]

def get_timestamp_utc(store_id,start_time,end_time, db=Depends(get_db)):
    start_time = start_time.astimezone(ZoneInfo("UTC"))
    end_time = end_time.astimezone(ZoneInfo("UTC"))
   # print(start_time, end_time)
    return db.query(Store_status).filter(
        Store_status.store_id == store_id,
        Store_status.timestamp_utc >= start_time,
        Store_status.timestamp_utc <= end_time
    ).order_by(Store_status.timestamp_utc).all()

def calculate_uptime(store_id,start_time,end_time,tz, db=Depends(get_db)):
    statuses = get_timestamp_utc(store_id,start_time,end_time, db)
    timestamps=[x.timestamp_utc.astimezone(tz) for x in statuses]
    

    total_uptime = 0
    total_downtime = 0
        
    if not timestamps:
        total_uptime=(end_time- start_time).total_seconds()/3600
        total_downtime= 0
    timestamps.insert(0, start_time)
    timestamps.append(end_time)
    
    for i in range(1,len(timestamps)-1):

        x=(timestamps[i + 1]-timestamps[i])/2
        y= (timestamps[i]-timestamps[i-1])/2
        if i==1:
            x=x*2
        if i==len(timestamps)-2:
            y=y*2
        if statuses[i-1].status == 'active':
            total_uptime += (x+y).total_seconds()/3600
        else:
            total_downtime +=(x+y).total_seconds()/3600

    return {
        "total_uptime":total_uptime,
        "total_downtime":total_downtime
    }

def start_calculation(store_id,curr_time,start,db=Depends(get_db)):
    tz= db.query(Timezone.timezone_str).filter(
        Timezone.store_id == store_id
    ).first()
    timezone_str = tz[0] if tz else 'America/Chicago'

    tz = ZoneInfo(timezone_str)
    local_curr_time = curr_time.astimezone(tz)
    total_uptime = 0
    total_downtime = 0
    d=start
    while d<= local_curr_time:


        business_hours = get_business_hour_interval(store_id, d.weekday(), db)
        if not business_hours:
            business_hours = [(datetime.min.time(), datetime.max.time())] 
        for bh in business_hours:
            
            start_time=datetime.combine(d.date(), bh[0]).replace(tzinfo=tz)
            end_time=datetime.combine(d.date(), bh[1]).replace(tzinfo=tz)

            if start> start_time:
                start_time = start
            if start> end_time or start_time>local_curr_time:
                continue
            if end_time>local_curr_time:
                end_time=local_curr_time
            
            case = calculate_uptime(store_id, start_time, end_time,tz, db)
            total_uptime+=case['total_uptime']
            total_downtime+=case['total_downtime']
        d = (d + timedelta(days=1))
        

    return {
        "total_uptime": total_uptime,
        "total_downtime": total_downtime
    }

def generate_report( report_id, db=Depends(get_db)):
    db.add(Report(report_id=report_id, status='Running'))
    db.commit()
    q1 = select(Store_status.store_id)
    q2 = select(Menu_hours.store_id)
    q3 = select(Timezone.store_id)

    stmt = union(q1, q2, q3)
    stores = db.execute(stmt).scalars().all()

    buffer = io.BytesIO()
    stream=io.TextIOWrapper(buffer, encoding='utf-8', newline='')
    writer = csv.writer(stream)

    writer.writerow(["Store ID", "Last Week Uptime(hrs)", "Last Week Downtime(hrs)", "Last Day Uptime(hrs)", "Last Day Downtime(hrs)", "Last Hour Uptime(mins)", "Last Hour Downtime(mins)"])
    for store in stores:
        store_id = store
        curr_time = datetime.fromisoformat("2024-10-14 08:00:18.727055+00:00")


        start = curr_time - timedelta(days=7)
        last_week = start_calculation(store_id, curr_time, start, db)
        
        start = curr_time - timedelta(days=1)
        last_day = start_calculation(store_id, curr_time, start, db)
        
        start = curr_time - timedelta(hours=1)
        last_hour = start_calculation(store_id, curr_time, start, db)   

        # Write the report
        writer.writerow([
            store_id,
            last_week['total_uptime'],
            last_week['total_downtime'],
            last_day['total_uptime'],
            last_day['total_downtime'],
            last_hour['total_uptime']*60,
            last_hour['total_downtime']*60
        ])
        
    stream.flush()
    buffer.seek(0)
    
    
    db.query(Report).filter(Report.report_id == report_id).update({"status": "Completed", "file": buffer.read()})
    db.commit()
    buffer.close()
    
    
    
