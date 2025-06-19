from sqlalchemy import Column, Integer, String, LargeBinary,Time,Index,DateTime,UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()


class Timezone(Base):
    __tablename__ = 'timezones'
    id = Column(Integer, primary_key=True,autoincrement=True)
    store_id= Column(String,index=True,unique=True)
    timezone_str=Column(String,default='USA/Chicago')
    
    
    __table_args__ = (
        Index('timezone_index', 'store_id'), 
    )
    
class Menu_hours(Base):
    __tablename__ = 'menu_hours'
    id = Column(Integer, primary_key=True, autoincrement=True)
    store_id = Column(String,  nullable=False)
    dayOfWeek = Column(Integer, nullable=False)
    start_time_local = Column(Time,default="00:00:00")
    end_time_local = Column(Time,default="23:59:59")
    

    __table_args__ = (
        Index('menu_hours_index', 'store_id', 'dayOfWeek'),
    )

class Store_status(Base):
    __tablename__ = 'store_status'

    id = Column(Integer, primary_key=True, autoincrement=True)
    store_id = Column(String,  nullable=False)
    status = Column(String, nullable=False)
    timestamp_utc = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index('store_status_index', 'store_id', 'timestamp_utc'),
    )

class Report(Base):
    __tablename__ = 'reports'
    report_id=Column(UUID, primary_key=True)
    status= Column(String, default='Running')
    file= Column(LargeBinary, nullable=True)
    