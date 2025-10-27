from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime

Base = declarative_base()

class CommandTripDB(Base):
    __tablename__ = 'command_trips'
    
    id = Column(Integer, primary_key=True)
    message_id = Column(String, unique=True)
    create_date = Column(DateTime)
    
class ReminderDB(Base):
    __tablename__ = 'reminders'
    
    id = Column(Integer, primary_key=True)
    command_trip_id = Column(Integer, ForeignKey('command_trips.id'))
    outlook_reminder_id = Column(String)
    reminder_date = Column(DateTime)