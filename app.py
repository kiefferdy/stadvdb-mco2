from flask import Flask, render_template, request
import sqlalchemy as sa
from sqlalchemy.orm import Session
import pandas as pd

# MySQL connection credentials
USERNAME = "root"
PASSWORD = "tCTDrUyJna2S4KRYN3bHqcmp"

# MySQL parameters
SCHEMA = "seriousmd"
TABLE = "seriousmd"

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('views/index.html')

@app.route('/appointments')
def appointments():
    search = request.args.get('search') or ""
    print("\trequest=" + search)

    engine = sa.create_engine("mysql+mysqldb://"+USERNAME+":"+PASSWORD+"@ccscloud.dlsu.edu.ph:20171/",
                              isolation_level="READ COMMITTED")

    # Currently selects the top 5 rows of table, TODO: change to search query
    stmt = sa.select(sa.text(f"*\nFROM {SCHEMA}.{TABLE}")).limit(5)
    # stmt = sa.select(sa.text(f"*\nFROM {SCHEMA}.{TABLE}")).where(sa.text(f""))

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
                           search_query=search,
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

if __name__ == '__main__':
    app.run(debug=True)