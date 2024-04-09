import threading
import sqlalchemy as sa
from sqlalchemy.orm import Session

# MySQL Connection Credentials
USERNAME = "root"
PASSWORD = "tCTDrUyJna2S4KRYN3bHqcmp"

# MySQL Database Parameters
SCHEMA = "seriousmd"
TABLE = "appointments"

# MySQL Database Engines
engines = [
    sa.create_engine(f"mysql+mysqldb://{USERNAME}:{PASSWORD}@ccscloud.dlsu.edu.ph:20171/"),
    sa.create_engine(f"mysql+mysqldb://{USERNAME}:{PASSWORD}@ccscloud.dlsu.edu.ph:20172/"),
    sa.create_engine(f"mysql+mysqldb://{USERNAME}:{PASSWORD}@ccscloud.dlsu.edu.ph:20173/")
]

def read_transaction(engine, apptid):
    session = Session(engine)
    with session.begin():
        with engine.connect() as conn:
            stmt = sa.text(f"SELECT * FROM {SCHEMA}.{TABLE} WHERE apptid = '{apptid}'")
            result = conn.execute(stmt).fetchall()
            print(f"Read transaction result: {result}")

def write_transaction(engine, apptid, status):
    session = Session(engine)
    with session.begin():
        with engine.connect() as conn:
            stmt = sa.text(f"UPDATE {SCHEMA}.{TABLE} SET status = '{status}' WHERE apptid = '{apptid}'")
            conn.execute(stmt)
            print(f"Write transaction executed: Updated status to '{status}' for apptid '{apptid}'")

def test_case_1():
    apptid = "APPT123"  # Specify the apptid to read
    threads = []
    for engine in engines:
        thread = threading.Thread(target=read_transaction, args=(engine, apptid))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()

def test_case_2():
    apptid = "APPT456"  # Specify the apptid to read and write
    threads = []
    for i, engine in enumerate(engines):
        if i == 0:
            thread = threading.Thread(target=write_transaction, args=(engine, apptid, "Complete"))
        else:
            thread = threading.Thread(target=read_transaction, args=(engine, apptid))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()

def test_case_3():
    apptid = "APPT789"  # Specify the apptid to write
    threads = []
    for engine in engines:
        thread = threading.Thread(target=write_transaction, args=(engine, apptid, "Cancel"))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()

# Run the test cases
test_case_1()
test_case_2()
test_case_3()