from flask import Flask, redirect, render_template, request, session, jsonify
from datetime import datetime
import sqlalchemy as sa
import pandas as pd
import random

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

# Initializes engines for each node
def init_engines():
    engine_url_template = f"mysql+pymysql://{USERNAME}:{PASSWORD}@{HOST}:{{port}}/{SCHEMA}"
    for node in nodes:
        try:
            engine_url = engine_url_template.format(port=node['id'])
            node["engine"] = sa.create_engine(engine_url, echo=False, pool_pre_ping=True)
        except Exception as e:
            node["online"] = False
            print(f"Warning: Offline note detected. Failed to connect to database on node {node['id']}: {e}")

init_engines()

# Gets engine based on user's selected node (will automatically switch node if selected node is offline)
def get_engine():
    node_id = session.get('selected_node', None)
    if node_id:
        node = next((node for node in nodes if node['id'] == node_id and node['online']), None)
        if node:
            return node['engine']

    # If no node is selected or selected node is offline, pick a new online node randomly
    new_node_id = get_random_online_node()
    if new_node_id is None:
        print("Error: All database nodes are currently offline!")
        return None

    session['selected_node'] = new_node_id
    return next(node['engine'] for node in nodes if node['id'] == new_node_id)

# Updates node statuses before every request
@app.before_request
def ensure_node_availability():
    update_node_status()
    selected_node_id = session.get('selected_node')
    if selected_node_id not in [node['id'] for node in nodes if node['online']]:
        new_node_id = get_random_online_node()
        if new_node_id is None:
            return jsonify({"error": "All database nodes are currently offline."}), 503
        session['selected_node'] = new_node_id

# Gets a random online node
def get_random_online_node():
    online_nodes = [node for node in nodes if node['online']]
    if not online_nodes:
        return None
    return random.choice(online_nodes)['id']

# Checks whether the specified node is online
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

# Updates the status of each node
def update_node_status():
    for node in nodes:
        node["online"] = ping_node(node["id"])

@app.route('/')
def home():
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
    selected_node = session.get('selected_node', 20171)
    search = request.args.get('search', default='')
    max_results = request.args.get('max_results', default=25, type=int)

    engine = get_engine()
    if not engine:
        return jsonify({"error": "All database nodes are currently offline."}), 503

    try:
        if search:
            sql = sa.text(f"SELECT * FROM {TABLE} WHERE pxid = :search OR doctorid = :search OR apptid = :search LIMIT :max_results")
        else:
            sql = sa.text(f"SELECT * FROM {TABLE} LIMIT :max_results")

        doctors_sql = sa.text(f"SELECT DISTINCT doctorid FROM {TABLE}")
        patients_sql = sa.text(f"SELECT DISTINCT pxid FROM {TABLE} LIMIT 500")
        clinics_sql = sa.text(f"SELECT DISTINCT clinicid FROM {TABLE}")

        with engine.begin() as conn:  # Begins a transaction
            df_appointments = pd.read_sql_query(sql, conn, params={'search': search, 'max_results': max_results})
            df_doctors = pd.read_sql_query(doctors_sql, conn)
            df_patients = pd.read_sql_query(patients_sql, conn)
            df_clinics = pd.read_sql_query(clinics_sql, conn)

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

@app.route('/appointments/create', methods=['POST'])
def create_appointment():
    engine = get_engine()
    if not engine:
        return jsonify({"error": "All database nodes are currently offline."}), 503

    try:
        # Insert the new appointment into the database
        stmt = sa.text(f"INSERT INTO {TABLE} (apptid, doctorid, pxid, clinicid, StartTime, EndTime, type, `Virtual`) VALUES (:apptid, :doctorid, :pxid, :clinicid, :start_time, :end_time, :type, :virtual)")

        with engine.begin() as conn:
            conn.execute(stmt, {
                'apptid': request.form['apptid'],
                'doctorid': request.form['doctor'],
                'pxid': request.form['patient'],
                'clinicid': request.form['clinic'],
                'start_time': request.form['start_time'],
                'end_time': request.form['end_time'],
                'type': request.form['type'],
                'status': request.form['status'],
                'virtual': 1 if 'virtual' in request.form else 0
            })

        return redirect('/appointments')

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/appointments/get/<apptid>')
def get_appointment(apptid):
    engine = get_engine()
    if not engine:
        return jsonify({"error": "All database nodes are currently offline."}), 503

    try:
        stmt = sa.text(f"SELECT * FROM {TABLE} WHERE apptid = :apptid")
        with engine.connect() as conn:
            result = conn.execute(stmt, {'apptid': apptid})
            appointment = result.fetchone()

        if appointment:
            appointment_dict = {
                "pxid": appointment[0],
                "clinicid": appointment[1],
                "doctorid": appointment[2],
                "apptid": appointment[3],
                "status": appointment[4],
                "TimeQueued": appointment[5].isoformat() if isinstance(appointment[5], datetime) else appointment[5],
                "QueueDate": appointment[6].isoformat() if isinstance(appointment[6], datetime) else appointment[6],
                "StartTime": appointment[7].isoformat() if isinstance(appointment[7], datetime) else appointment[7],
                "EndTime": appointment[8].isoformat() if isinstance(appointment[8], datetime) else appointment[8],
                "type": appointment[9],
                "Virtual": bool(appointment[10]),
                "hospitalname": appointment[11],
                "IsHospital": bool(appointment[12]),
                "City": appointment[13],
                "Province": appointment[14],
                "RegionName": appointment[15],
                "mainspecialty": appointment[16],
                "doctor_age": appointment[17],
                "patient_age": appointment[18],
                "patient_gender": appointment[19]
            }
            return jsonify(appointment_dict)
        else:
            return jsonify({"error": "Appointment not found."}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/appointments/update/<apptid>', methods=['POST'])
def update_appointment(apptid):
    engine = get_engine()
    if not engine:
        return jsonify({"error": "All database nodes are currently offline."}), 503

    try:
        # Update the appointment in the database
        stmt = sa.text(f"UPDATE {TABLE} SET doctorid = :doctorid, pxid = :pxid, clinicid = :clinicid, StartTime = :start_time, EndTime = :end_time, type = :type, `Virtual` = :virtual WHERE apptid = :apptid")

        with engine.begin() as conn:
            conn.execute(stmt, {
                'apptid': apptid,
                'doctorid': request.form['doctor'],
                'pxid': request.form['patient'],
                'clinicid': request.form['clinic'],
                'start_time': request.form['start_time'],
                'end_time': request.form['end_time'],
                'type': request.form['type'],
                'status': request.form['status'],
                'virtual': 1 if 'virtual' in request.form else 0
            })

        return redirect('/appointments')

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/appointments/delete/<apptid>', methods=['POST'])
def delete_appointment(apptid):
    engine = get_engine()
    if not engine:
        return jsonify({"error": "All database nodes are currently offline."}), 503

    try:
        # Delete the appointment from the database
        stmt = sa.text(f"DELETE FROM {TABLE} WHERE apptid = :apptid")

        with engine.begin() as conn:
            conn.execute(stmt, {'apptid': apptid})

        return redirect('/appointments')

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/doctors')
def doctors():
    selected_node = session.get('selected_node', 20171)
    search = request.args.get('search', default='')
    max_results = request.args.get('max_results', default=25, type=int)

    engine = get_engine()
    if not engine:
        return jsonify({"error": "All database nodes are currently offline."}), 503

    try:
        if search:
            sql = sa.text(f"SELECT DISTINCT doctorid, mainspecialty, doctor_age FROM {TABLE} WHERE doctorid = :search ORDER BY doctorid LIMIT :max_results")
        else:
            sql = sa.text(f"SELECT DISTINCT doctorid, mainspecialty, doctor_age FROM {TABLE} ORDER BY doctorid LIMIT :max_results")

        with engine.begin() as conn:
            df_doctors = pd.read_sql_query(sql, conn, params={'search': search, 'max_results': max_results})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return render_template('views/doctors.html',
                           nodes=nodes,
                           selected_node=selected_node,
                           search_query=search if search else "",
                           max_results=max_results,
                           doctors=df_doctors)

@app.route('/patients')
def patients():
    selected_node = session.get('selected_node', 20171)
    search = request.args.get('search', default='')
    max_results = request.args.get('max_results', default=25, type=int)

    engine = get_engine()
    if not engine:
        return jsonify({"error": "All database nodes are currently offline."}), 503

    try:
        if search:
            sql = sa.text(f"SELECT DISTINCT pxid, patient_gender, patient_age FROM {TABLE} WHERE pxid = :search ORDER BY pxid LIMIT :max_results")
        else:
            sql = sa.text(f"SELECT DISTINCT pxid, patient_gender, patient_age FROM {TABLE} ORDER BY pxid LIMIT :max_results")

        with engine.begin() as conn:
            df_patients = pd.read_sql_query(sql, conn, params={'search': search, 'max_results': max_results})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return render_template('views/patients.html',
                           nodes=nodes,
                           selected_node=selected_node,
                           search_query=search if search else "",
                           max_results=max_results,
                           patients=df_patients)

@app.route('/clinics')
def clinics():
    selected_node = session.get('selected_node', 20171)
    search = request.args.get('search', default='')
    max_results = request.args.get('max_results', default=25, type=int)

    engine = get_engine()
    if not engine:
        return jsonify({"error": "All database nodes are currently offline."}), 503

    try:
        if search:
            sql = sa.text(f"SELECT DISTINCT clinicid, hospitalname, City, Province, RegionName FROM {TABLE} WHERE clinicid = :search ORDER BY clinicid LIMIT :max_results")
        else:
            sql = sa.text(f"SELECT DISTINCT clinicid, hospitalname, City, Province, RegionName FROM {TABLE} ORDER BY clinicid LIMIT :max_results")

        with engine.begin() as conn:
            df_clinics = pd.read_sql_query(sql, conn, params={'search': search, 'max_results': max_results})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return render_template('views/clinics.html',
                           nodes=nodes,
                           selected_node=selected_node,
                           search_query=search if search else "",
                           max_results=max_results,
                           clinics=df_clinics)

if __name__ == '__main__':
    app.run(debug=True)