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
            CREATE TABLE IF NOT EXISTS appointments (
                pxid           VARCHAR(32),
                clinicid       VARCHAR(32),
                doctorid       VARCHAR(32),
                apptid         VARCHAR(32) NOT NULL UNIQUE,
                status         ENUM('Cancel', 'Complete', 'NoShow', 'Queued', 'Serving', 'Skip') NOT NULL,
                TimeQueued     DATETIME,
                QueueDate      DATETIME,
                StartTime      DATETIME,
                EndTime        DATETIME,
                type           ENUM('Consultation', 'Inpatient') NOT NULL,
                `Virtual`      BOOLEAN,
                hospitalname   TEXT,
                IsHospital     BOOLEAN,
                City           TEXT,
                Province       TEXT,
                RegionName     TEXT,
                mainspecialty  TEXT,
                doctor_age     INT UNSIGNED,
                patient_age    INT UNSIGNED,
                patient_gender ENUM('MALE', 'FEMALE'),
                PRIMARY KEY (apptid)
            )
        """))

start_time = time.time()

# Create seriousmd Schemas
create_seriousmd_schema()
print(f"Created seriousmd schema in {time.time() - start_time:.2f} seconds")

start_time = time.time()

# Load seriousMD.csv into a DataFrame
df = pd.read_csv('../data/seriousmd.csv')
print(f"Loaded seriousMD.csv into DataFrame in {time.time() - start_time:.2f} seconds")

start_time = time.time()

# Insert DataFrame into appointments table
df.to_sql('appointments', con=engine, schema='seriousmd', if_exists='append', index=False)
print(f"Inserted DataFrame into appointments table in {time.time() - start_time:.2f} seconds")

# Close the database connection
engine.dispose()