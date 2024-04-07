import pandas as pd #TO IMPORT: pip install pandas
import sqlalchemy as sa # TO IMPORT: pip install sqlalchemy
from sqlalchemy import text
from datetime import datetime
import time

# MySQL connection credentials
USERNAME = "root"
PASSWORD = "tCTDrUyJna2S4KRYN3bHqcmp"

engine = sa.create_engine("mysql+mysqldb://"+USERNAME+":"+PASSWORD+"@ccscloud.dlsu.edu.ph:20171/")

def create_seriousmd_schema():
    with engine.connect() as connection:
        connection.execute(text("CREATE DATABASE IF NOT EXISTS seriousmd"))
        connection.execute(text("USE seriousmd"))
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS seriousmd (
                pxid VARCHAR(255),
                clinicid VARCHAR(255),
                doctorid VARCHAR(255),
                apptid VARCHAR(255),
                status VARCHAR(255),
                TimeQueued VARCHAR(255),
                QueueDate VARCHAR(255),
                StartTime VARCHAR(255),
                EndTime VARCHAR(255),
                type VARCHAR(255),
                px_gender VARCHAR(255),
                hospitalname VARCHAR(255),
                City VARCHAR(255),
                Province VARCHAR(255),
                RegionName VARCHAR(255),
                mainspecialty VARCHAR(255),
                is_virtual BOOLEAN,
                IsHospital INT,
                px_age INT,
                doc_age INT
            )
        """))
        
        
# Create seriousmd Schemas

start_time = time.time()

# Create seriousmd Schemas
create_seriousmd_schema()
print(f"Created seriousmd schema in {time.time() - start_time:.2f} seconds")

start_time = time.time()

# Load seriousMD.csv into a DataFrame
df = pd.read_csv('seriousMD.csv')
print(f"Loaded seriousMD.csv into DataFrame in {time.time() - start_time:.2f} seconds")

start_time = time.time()

# Insert DataFrame into seriousmd table
df.to_sql('seriousmd', con=engine, schema='seriousmd', if_exists='append', index=False)
print(f"Inserted DataFrame into seriousmd table in {time.time() - start_time:.2f} seconds")

# Close the database connection
engine.dispose()    