from flask import Flask, render_template, request
import sqlalchemy as sa
from sqlalchemy.orm import Session
import pandas as pd

# MySQL connection credentials
USERNAME = "root"
PASSWORD = "tCTDrUyJna2S4KRYN3bHqcmp"

# MySQL parameters
SCHEMA = "seriousmd"
TABLE = "appointments"
PORT = 20171

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('views/index.html')

@app.route('/appointments')
def appointments():
    search = request.args.get('search')

    engine = sa.create_engine(f"mysql+mysqldb://{USERNAME}:{PASSWORD}@ccscloud.dlsu.edu.ph:{PORT}/",
                              isolation_level="READ COMMITTED")

    stmt_appointments = sa.text(f"SELECT *\nFROM {SCHEMA}.{TABLE}\nWHERE pxid = '{search}' OR doctorid = '{search}'")
    df_appointments = None
    session = Session(engine)
    with session.begin():
        with engine.connect() as conn:
            df_appointments = pd.read_sql_query(stmt_appointments, conn)
    
    # Fetch unique doctor IDs
    stmt_doctors = sa.text(f"SELECT DISTINCT doctorid FROM {SCHEMA}.{TABLE}")
    df_doctors = pd.read_sql_query(stmt_doctors, engine)
    
    # Fetch unique patient IDs
    stmt_patients = sa.text(f"SELECT DISTINCT pxid FROM {SCHEMA}.{TABLE}")
    df_patients = pd.read_sql_query(stmt_patients, engine)
    
    # Fetch unique clinic IDs
    stmt_clinics = sa.text(f"SELECT DISTINCT clinicid FROM {SCHEMA}.{TABLE}")
    df_clinics = pd.read_sql_query(stmt_clinics, engine)
    
    # Close the database connection
    engine.dispose()

    return render_template('views/appointments.html', 
                           search_query=search if search else "", 
                           appointments=df_appointments,
                           doctors=df_doctors,
                           patients=df_patients,
                           clinics=df_clinics)

@app.route('/doctors')
def doctors():
    search = request.args.get('search')

    engine = sa.create_engine(f"mysql+mysqldb://{USERNAME}:{PASSWORD}@ccscloud.dlsu.edu.ph:{PORT}/",
                              isolation_level="READ COMMITTED")

    stmt = sa.text(f"SELECT DISTINCT doctorid, mainspecialty, doctor_age FROM {SCHEMA}.{TABLE} ORDER BY doctorid;")

    df = None

    session = Session(engine)

    with session.begin():
        with engine.connect() as conn:
            df = pd.read_sql_query(
                stmt,
                conn
            )

    # Close the database connection
    engine.dispose()

    return render_template('views/doctors.html',
                           search_query=search if search else "",
                           doctors=df)

@app.route('/patients')
def patients():
    search = request.args.get('search')

    engine = sa.create_engine(f"mysql+mysqldb://{USERNAME}:{PASSWORD}@ccscloud.dlsu.edu.ph:{PORT}/",
                              isolation_level="READ COMMITTED")

    stmt = sa.text(f"SELECT DISTINCT pxid, patient_gender, patient_age FROM {SCHEMA}.{TABLE} ORDER BY pxid;")

    df = None

    session = Session(engine)

    with session.begin():
        with engine.connect() as conn:
            df = pd.read_sql_query(
                stmt,
                conn
            )

    # Close the database connection
    engine.dispose()
    return render_template('views/patients.html',
                           search_query=search if search else "",
                           patients=df)

@app.route('/clinics')
def clinics():
    search = request.args.get('search')

    engine = sa.create_engine(f"mysql+mysqldb://{USERNAME}:{PASSWORD}@ccscloud.dlsu.edu.ph:{PORT}/",
                              isolation_level="READ COMMITTED")

    stmt = sa.text(f"SELECT DISTINCT clinicid, hospitalname, IsHospital, City, Province, RegionName FROM {SCHEMA}.{TABLE} ORDER BY clinicid;")

    df = None

    session = Session(engine)

    with session.begin():
        with engine.connect() as conn:
            df = pd.read_sql_query(
                stmt,
                conn
            )

    # Close the database connection
    engine.dispose()
    return render_template('views/clinics.html',
                           search_query=search if search else "",
                           clinics=df)

@app.route('/concurrency1')
def concurrency1():
    status = request.args.get('status')
    level = request.args.get('level')
    return render_template('views/concurrency1.html', status=status, level=level)

if __name__ == '__main__':
    app.run(debug=True)