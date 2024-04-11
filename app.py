from flask import Flask, redirect, render_template, request, session, jsonify
import sqlalchemy as sa
import pandas as pd

# MySQL Database Config
HOST = "ccscloud.dlsu.edu.ph"
USERNAME = "root"
PASSWORD = "tCTDrUyJna2S4KRYN3bHqcmp"
SCHEMA = "seriousmd"
TABLE = "appointments"

# MySQL Database Nodes
nodes = [
    {"id": 20171, "online": True, "engine": None},
    {"id": 20172, "online": True, "engine": None},
    {"id": 20173, "online": True, "engine": None},
]

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'MqWHf-e4QGyS7_xq4BiA9Qbs-0F4ADEH'

# Initialize engines for each node
def init_engines():
    engine_url_template = f"mysql+pymysql://{USERNAME}:{PASSWORD}@{HOST}:{{port}}/{SCHEMA}"
    for node in nodes:
        if node["online"]:
            try:
                engine_url = engine_url_template.format(port=node['id'])
                node["engine"] = sa.create_engine(engine_url, echo=True, pool_pre_ping=True)
            except Exception as e:
                node["online"] = False
                print(f"Failed to connect to database on node {node['id']}: {e}")

init_engines()

# Function to get engine based on user's selected node
def get_engine():
    node_id = session.get('selected_node', 20171)
    for node in nodes:
        if node['id'] == node_id:
            return node['engine']
    return None

# Function to check if any node is offline
def ping_node(node_id):
    for node in nodes:
        if node['id'] == node_id:
            try:
                with node["engine"].connect() as conn:
                    return True
            except Exception as e:
                node["online"] = False
                print(f"Node {node_id} is offline: {e}")
                return False
    return False

# Function to update node statuses
def update_node_status():
    for node in nodes:
        node["online"] = ping_node(node["id"])

# -------
# ROUTERS
# -------

@app.route('/')
def home():
    update_node_status()
    selected_node = session.get('selected_node', 20171)
    return render_template('views/index.html', nodes=nodes, selected_node=selected_node)

@app.route('/status')
def getServerStatus():
    update_node_status()
    stmt = sa.text("SELECT COUNT(*) as 'ActiveCount' FROM INFORMATION_SCHEMA.INNODB_TRX WHERE trx_query NOT LIKE 'SELECT * FROM INFORMATION_SCHEMA.INNODB_TRX%';")
    data = {}
    for node in nodes:
        if node["online"]:  # Only attempt to query nodes that are marked online
            try:
                engine = node["engine"]
                with engine.begin() as conn:
                    result = conn.execute(stmt)
                    active_count = result.scalar()
                    data[str(node['id'])] = active_count > 0
            except Exception as e:
                node["online"] = False  # Mark the node as offline if any error occurs
                print(f"Error querying node {node['id']}: {e}")
                data[str(node['id'])] = False
        else:
            data[str(node['id'])] = False  # If the node is offline, set its status as False in the response
    return jsonify(data)

@app.route('/set_node')
def set_node():
    node = request.args.get('node', default=20171, type=int)
    session['selected_node'] = node
    return redirect(request.referrer)

@app.route('/appointments')
def appointments():
    update_node_status()
    selected_node = session.get('selected_node', 20171)
    search = request.args.get('search', default='')
    max_results = request.args.get('max_results', default=25, type=int)

    engine = get_engine()
    if not engine:
        return jsonify({"error": "Database connection error"}), 500

    try:
        if search:
            sql = sa.text(f"SELECT * FROM {TABLE} WHERE pxid = :search OR doctorid = :search OR apptid = :search LIMIT :max_results")
        else:
            sql = sa.text(f"SELECT * FROM {TABLE} LIMIT :max_results")

        with engine.begin() as conn:  # Begins a transaction
            df_appointments = pd.read_sql_query(sql, conn, params={'search': search, 'max_results': max_results})

        df_doctors = pd.DataFrame(df_appointments['doctorid'].unique(), columns=['doctorid'])
        df_patients = pd.DataFrame(df_appointments['pxid'].unique(), columns=['pxid'])
        df_clinics = pd.DataFrame(df_appointments['clinicid'].unique(), columns=['clinicid'])

    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
    update_node_status()
    selected_node = session.get('selected_node', 20171)
    max_results = request.args.get('max_results', default=25, type=int)

    engine = get_engine()
    if not engine:
        return jsonify({"error": "Database connection error"}), 500

    try:
        sql = sa.text(f"SELECT DISTINCT doctorid, mainspecialty, doctor_age FROM {TABLE} ORDER BY doctorid LIMIT :max_results")
        with engine.begin() as conn:
            df_doctors = pd.read_sql_query(sql, conn, params={'max_results': max_results})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return render_template('views/doctors.html',
                           nodes=nodes,
                           selected_node=selected_node,
                           max_results=max_results,
                           doctors=df_doctors)

@app.route('/patients')
def patients():
    update_node_status()
    selected_node = session.get('selected_node', 20171)
    max_results = request.args.get('max_results', default=25, type=int)

    engine = get_engine()
    if not engine:
        return jsonify({"error": "Database connection error"}), 500

    try:
        sql = sa.text(f"SELECT DISTINCT pxid, patient_gender, patient_age FROM {TABLE} ORDER BY pxid LIMIT :max_results")
        with engine.begin() as conn:
            df_patients = pd.read_sql_query(sql, conn, params={'max_results': max_results})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return render_template('views/patients.html',
                           nodes=nodes,
                           selected_node=selected_node,
                           max_results=max_results,
                           patients=df_patients)

@app.route('/clinics')
def clinics():
    update_node_status()
    selected_node = session.get('selected_node', 20171)
    max_results = request.args.get('max_results', default=25, type=int)

    engine = get_engine()
    if not engine:
        return jsonify({"error": "Database connection error"}), 500

    try:
        sql = sa.text(f"SELECT DISTINCT clinicid, hospitalname, City, Province, RegionName FROM {TABLE} ORDER BY clinicid LIMIT :max_results")
        with engine.begin() as conn:
            df_clinics = pd.read_sql_query(sql, conn, params={'max_results': max_results})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return render_template('views/clinics.html',
                           nodes=nodes,
                           selected_node=selected_node,
                           max_results=max_results,
                           clinics=df_clinics)

if __name__ == '__main__':
    app.run(debug=True)