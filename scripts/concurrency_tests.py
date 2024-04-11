import time
import threading
import sqlalchemy as sa
import sqlalchemy.exc

# MySQL Connection Credentials
USERNAME = "root"
PASSWORD = "tCTDrUyJna2S4KRYN3bHqcmp"

# MySQL Database Parameters
SCHEMA = "seriousmd"
TABLE = "appointments"

# MySQL Database Nodes
nodes = [
    {"id": 20171, "engine": None},
    {"id": 20172, "engine": None},
    {"id": 20173, "engine": None},
]

# Function to create engine for each node
def create_engine(node_id):
    return sa.create_engine(f"mysql+mysqldb://{USERNAME}:{PASSWORD}@ccscloud.dlsu.edu.ph:{node_id}/")

# Read transaction
def read_transaction(node_id, apptid):
    engine = nodes[node_id - 20171]["engine"]
    with engine.begin() as conn:
        stmt = sa.text(f"SELECT * FROM {SCHEMA}.{TABLE} WHERE apptid = :apptid").bindparams(apptid=apptid)
        result = conn.execute(stmt).fetchall()
        print(f"[Node {node_id}] Read transaction result: {result}\n")

# Write transaction
def write_transaction(node_id, apptid, status):
    engine = nodes[node_id - 20171]["engine"]
    with engine.begin() as conn:  # Automatically begins and commits/rollbacks transactions
        stmt = sa.text(f"UPDATE {SCHEMA}.{TABLE} SET status = :status WHERE apptid = :apptid").bindparams(status=status, apptid=apptid)
        result = conn.execute(stmt)
        rows_affected = result.rowcount
        print(f"[Node {node_id}] Write transaction executed: {'Updated' if rows_affected > 0 else 'No'} rows affected for apptid '{apptid}' with status '{status}'.\n")

# Write transaction and retry in the case of deadlock
def write_transaction_with_retry(node_id, apptid, status, max_attempts=5):
    attempt = 0
    engine = nodes[node_id - 20171]["engine"]
    while attempt < max_attempts:
        try:
            with engine.begin() as conn:
                stmt = sa.text(f"UPDATE {SCHEMA}.{TABLE} SET status = :status WHERE apptid = :apptid").bindparams(status=status, apptid=apptid)
                result = conn.execute(stmt)
                rows_affected = result.rowcount
                print(f"[Node {node_id}] Write transaction executed: {'Updated' if rows_affected > 0 else 'No'} rows affected for apptid '{apptid}' with status '{status}'.\n")
                # If we reach this point, the transaction was successful, so break the loop
                break
        except sqlalchemy.exc.OperationalError as e:
            if 'Deadlock found' in str(e):
                print(f"Deadlock detected in write_transaction on node {node_id}, attempt {attempt + 1}. Retrying...\n")
                time.sleep(0.1 * attempt)  # Exponential backoff could be considered here
                attempt += 1
            else:
                # If the exception is not a deadlock, re-raise it
                raise e
    else:
        # Handle failure if all attempts have been exhausted
        print(f"Failed to complete write_transaction on node {node_id} after {max_attempts} attempts due to deadlocks.\n")


def test_case_1():
    print("==========================================================================================")
    print("Test Case #1: Concurrent transactions in two or more nodes are reading the same data item.")
    print("==========================================================================================\n")
    apptid = "000019E8D2903D7A8D69B782507287E7"  # Specify the apptid to read
    threads = []
    for node in nodes:
        thread = threading.Thread(target=read_transaction, args=(node["id"], apptid))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()

def test_case_2():
    print("============================================================================================================================================================")
    print("Test Case #2: At least one transaction in the three nodes is writing (update/delete) and the other concurrent transactions are reading the same data item.")
    print("============================================================================================================================================================\n")
    apptid = "0000898824452C2A9911EB89BE398099"  # Specify the apptid to read and write
    threads = []
    for i, node in enumerate(nodes):
        if i == 0:
            thread = threading.Thread(target=write_transaction, args=(node["id"], apptid, "Cancel"))
        else:
            thread = threading.Thread(target=read_transaction, args=(node["id"], apptid))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()

def test_case_3():
    print("==========================================================================================================")
    print("Test Case #3: Concurrent transactions in two or more nodes are writing (update/delete) the same data item.")
    print("==========================================================================================================\n")
    apptid = "00038F63FCBF2233D5D5ECC39BE31D7F"  # Specify the apptid to write
    statuses = ["Complete", "Skip", "NoShow"]  # Define different statuses for each transaction
    threads = []

    for node, status in zip(nodes, statuses):
        thread = threading.Thread(target=write_transaction_with_retry, args=(node["id"], apptid, status))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

# Create engines for each node
for node in nodes:
    node["engine"] = create_engine(node["id"])

# Run the test cases
test_case_1()
test_case_2()
test_case_3()

# Close all database connections
for node in nodes:
    node["engine"].dispose()