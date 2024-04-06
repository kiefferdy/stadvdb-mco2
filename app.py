from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('views/index.html')

@app.route('/appointments')
def appointments():
    return render_template('views/appointments.html')

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