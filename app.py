from flask import Flask, redirect, render_template, request, session, jsonify
import sqlalchemy as sa
import pymysql
from sqlalchemy.orm import Session
import pandas as pd

# MySQL Connection Credentials
USERNAME = "root"
PASSWORD = "tCTDrUyJna2S4KRYN3bHqcmp"

# MySQL Database Parameters
SCHEMA = "seriousmd"
TABLE = "appointments"

# MySQL Database Nodes
nodes = [
    {"id": 20171, "online": True},
    {"id": 20172, "online": True},
    {"id": 20173, "online": True},
]

app = Flask(__name__)
app.secret_key = 'MqWHf-e4QGyS7_xq4BiA9Qbs-0F4ADEH'

# Function to get engine based on user's selected node
def get_engine():
    node = session.get('selected_node', 20171)
    return sa.create_engine(f"mysql+mysqldb://{USERNAME}:{PASSWORD}@ccscloud.dlsu.edu.ph:{node}/")

# Function to check if any node is offline

def ping_node(node_id):
    try:
        connection = pymysql.connect(
            host=f"ccscloud.dlsu.edu.ph",
            port=node_id,
            user=USERNAME,
            password=PASSWORD,
            database=SCHEMA,
            connect_timeout=2
        )
        connection.close()
        return True
    except pymysql.Error:
        return False

# Function to update node status in web UI
def update_node_status():
    for node in nodes:
        node["online"] = ping_node(node["id"])

# -------
# ROUTERS
# -------

@app.route('/')
def home():
    selected_node = session.get('selected_node', 20171)
    return render_template('views/index.html', nodes=nodes, selected_node=selected_node)

@app.route('/node_status')
def node_status():
    update_node_status()
    return jsonify({"nodes": nodes})

@app.route('/set_node')
def set_node():
    node = request.args.get('node', default=20171, type=int)
    session['selected_node'] = node
    return redirect(request.referrer)

@app.route('/appointments')
def appointments():
    selected_node = session.get('selected_node', 20171)
    search = request.args.get('search', default='')
    max_results = request.args.get('max_results', default=25, type=int)

    if search == '' or search is None:
        stmt_appointments = sa.text(f"SELECT *\nFROM {SCHEMA}.{TABLE}\nLIMIT {max_results}")
    else:
        stmt_appointments = sa.text(f"SELECT *\nFROM {SCHEMA}.{TABLE}\nWHERE pxid = '{search}' OR doctorid = '{search}' OR apptid = '{search}'\nLIMIT {max_results}")


    df_appointments = None
    engine = get_engine()
    db_session = Session(engine)
    with db_session.begin():
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
                           nodes=nodes,
                           selected_node=selected_node,
                           search_query=search if search else "",
                           max_results=max_results,
                           appointments=df_appointments,
                           doctors=df_doctors,
                           patients=df_patients,
                           clinics=df_clinics)

@app.route('/doctors')
def doctors():
    selected_node = session.get('selected_node', 20171)
    search = request.args.get('search')
    max_results = request.args.get('max_results', default=25, type=int)

    stmt = sa.text(f"SELECT DISTINCT doctorid, mainspecialty, doctor_age FROM {SCHEMA}.{TABLE} ORDER BY doctorid\nLIMIT {max_results};")

    df = None
    engine = get_engine()
    db_session = Session(engine)
    with db_session.begin():
        with engine.connect() as conn:
            df = pd.read_sql_query(
                stmt,
                conn
            )

    # Close the database connection
    engine.dispose()
    return render_template('views/doctors.html',
                           nodes=nodes,
                           selected_node=selected_node,
                           search_query=search if search else "",
                           max_results=max_results,
                           doctors=df)

@app.route('/patients')
def patients():
    selected_node = session.get('selected_node', 20171)
    search = request.args.get('search')
    max_results = request.args.get('max_results', default=25, type=int)

    stmt = sa.text(f"SELECT DISTINCT pxid, patient_gender, patient_age FROM {SCHEMA}.{TABLE} ORDER BY pxid\nLIMIT {max_results};")

    df = None
    engine = get_engine()
    db_session = Session(engine)
    with db_session.begin():
        with engine.connect() as conn:
            df = pd.read_sql_query(
                stmt,
                conn
            )

    # Close the database connection
    engine.dispose()
    return render_template('views/patients.html',
                           nodes=nodes,
                           selected_node=selected_node,
                           search_query=search if search else "",
                           max_results=max_results,
                           patients=df)

@app.route('/clinics')
def clinics():
    selected_node = session.get('selected_node', 20171)
    search = request.args.get('search')
    max_results = request.args.get('max_results', default=25, type=int)

    stmt = sa.text(f"SELECT DISTINCT clinicid, hospitalname, IsHospital, City, Province, RegionName FROM {SCHEMA}.{TABLE} ORDER BY clinicid\nLIMIT {max_results};")

    df = None
    engine = get_engine()
    db_session = Session(engine)
    with db_session.begin():
        with engine.connect() as conn:
            df = pd.read_sql_query(
                stmt,
                conn
            )

    # Close the database connection
    engine.dispose()
    return render_template('views/clinics.html',
                           nodes=nodes,
                           selected_node=selected_node,
                           search_query=search if search else "",
                           max_results=max_results,
                           clinics=df)

@app.route('/concurrency1')
def concurrency1():
    status = request.args.get('status')
    level = request.args.get('level')
    return render_template('views/concurrency1.html', status=status, level=level)

@app.route('/status')
def getServerStatus():
    stmt = sa.text("SELECT COUNT(*) as 'ActiveCount' FROM INFORMATION_SCHEMA.INNODB_TRX WHERE trx_query NOT LIKE 'SELECT * FROM INFORMATION_SCHEMA.INNODB_TRX%';")
    data = {}
    for i in range(1, 3 + 1):
        eng = sa.create_engine(f"mysql+mysqldb://{USERNAME}:{PASSWORD}@ccscloud.dlsu.edu.ph:2017{i}/")
        session = Session(bind=eng)
        with session.begin():
            session.connection(execution_options={"isolation_level": "READ UNCOMMITTED"})
            main = pd.read_sql_query(stmt, eng)
        data[str(i)] = True if main.iloc[0]['ActiveCount'] > 0 else False
    return jsonify(data)

@app.route('/delete_appointment/<apptid>', methods=['POST'])
def delete_appointment(apptid):
    selected_node = session.get('selected_node', 20171)
    engine = get_engine()
    db_session = Session(engine)

    try:
        # Delete the appointment from the database
        stmt = sa.text(f"DELETE FROM {SCHEMA}.{TABLE} WHERE apptid = :apptid")
        with db_session.begin():
            with engine.connect() as conn:
                conn.execute(stmt, {'apptid': apptid})
    except Exception as e:
        # Handle any exceptions that occur during the database operation
        print(f"An error occurred: {str(e)}")
    finally:
        # Close the database connection
        engine.dispose()
        
    return redirect('/appointments')

@app.route('/edit_appointment/<apptid>', methods=['POST'])
def edit_appointment(apptid):
    selected_node = session.get('selected_node', 20171)
    engine = get_engine()
    db_session = Session(engine)

    # Update the appointment in the database
    stmt = sa.text(f"UPDATE {SCHEMA}.{TABLE} SET doctorid = :doctorid, pxid = :pxid, clinicid = :clinicid, StartTime = :start_time, EndTime = :end_time, type = :type, `Virtual` = ':virtual' WHERE apptid = :apptid")
    with db_session.begin():
        with engine.connect() as conn:
            conn.execute(stmt, {
                'apptid': apptid,
                'doctorid': request.form['doctor'],
                'pxid': request.form['patient'],
                'clinicid': request.form['clinic'],
                'start_time': request.form['start_time'],
                'end_time': request.form['end_time'],
                'type': request.form['type'],
                'virtual': 1 if 'virtual' in request.form else 0
            })

    engine.dispose()
    return redirect('/appointments')

if __name__ == '__main__':
    app.run(debug=True)