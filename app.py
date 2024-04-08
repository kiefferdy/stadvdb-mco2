from flask import Flask, render_template, request
import sqlalchemy as sa
from sqlalchemy.orm import Session
import pandas as pd

# MySQL Connection Credentials
USERNAME = "root"
PASSWORD = "tCTDrUyJna2S4KRYN3bHqcmp"

# MySQL Database Parameters
SCHEMA = "seriousmd"
TABLE = "appointments"
PORT = 20171 # Can be 20171, 20172, or 20173

# MySQL Database Engine
engine = sa.create_engine(f"mysql+mysqldb://{USERNAME}:{PASSWORD}@ccscloud.dlsu.edu.ph:{PORT}/")

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('views/index.html')

@app.route('/appointments')
def appointments():
    search = request.args.get('search', default='')
    max_results = request.args.get('max_results', default=25, type=int)

    if search == '' or search is None:
        stmt_appointments = sa.text(f"SELECT *\nFROM {SCHEMA}.{TABLE}\nLIMIT {max_results}")
    else:
        stmt_appointments = sa.text(f"SELECT *\nFROM {SCHEMA}.{TABLE}\nWHERE pxid = '{search}' OR doctorid = '{search}' OR apptid = '{search}'\nLIMIT {max_results}")


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
                           max_results=max_results,
                           appointments=df_appointments,
                           doctors=df_doctors,
                           patients=df_patients,
                           clinics=df_clinics)

@app.route('/doctors')
def doctors():
    search = request.args.get('search')
    max_results = request.args.get('max_results', default=25, type=int)

    stmt = sa.text(f"SELECT DISTINCT doctorid, mainspecialty, doctor_age FROM {SCHEMA}.{TABLE} ORDER BY doctorid\nLIMIT {max_results};")

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
                           max_results=max_results,
                           doctors=df)

@app.route('/patients')
def patients():
    search = request.args.get('search')
    max_results = request.args.get('max_results', default=25, type=int)

    stmt = sa.text(f"SELECT DISTINCT pxid, patient_gender, patient_age FROM {SCHEMA}.{TABLE} ORDER BY pxid\nLIMIT {max_results};")

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
                           max_results=max_results,
                           patients=df)

@app.route('/clinics')
def clinics():
    search = request.args.get('search')
    max_results = request.args.get('max_results', default=25, type=int)

    stmt = sa.text(f"SELECT DISTINCT clinicid, hospitalname, IsHospital, City, Province, RegionName FROM {SCHEMA}.{TABLE} ORDER BY clinicid\nLIMIT {max_results};")

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
                           max_results=max_results,
                           clinics=df)

@app.route('/concurrency1')
def concurrency1():
    status = request.args.get('status')
    level = request.args.get('level')
    return render_template('views/concurrency1.html', status=status, level=level)

if __name__ == '__main__':
    app.run(debug=True)