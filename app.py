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

if __name__ == '__main__':
    app.run(debug=True)