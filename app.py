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

    stmt = sa.text(f"SELECT *\nFROM {SCHEMA}.{TABLE}\nWHERE pxid = '{search}' OR doctorid = '{search}'")

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

    return render_template('views/appointments.html',
                           search_query=search if search else "",
                           appointments=df
                           )

@app.route('/doctors')
def doctors():
    return render_template('views/doctors.html')

@app.route('/patients')
def patients():
    return render_template('views/patients.html')

@app.route('/clinics')
def clinics():
    return render_template('views/clinics.html')

@app.route('/concurrency1')
def concurrency1():
    status = request.args.get('status')
    level = request.args.get('level')
    return render_template('views/concurrency1.html', status=status, level=level)

if __name__ == '__main__':
    app.run(debug=True)