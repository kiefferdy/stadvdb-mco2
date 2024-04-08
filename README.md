# STADVDB MCO2

Instructions to run:

- Install python 3.12
- Create a virtual environment with `python -m venv venv`
- Activate the virtual environment by running `venv/Scripts/activate` (Might need to enclose with `"venv/Scripts/activate"`)
- Install dependencies with `pip install -r requirements.txt`
- Run development server with `flask run --debug`. The server is hosted on `localhost:5000` or `127.0.0.1:5000` by default.
- Once finished, run `deactivate` to exit the virtual environment

To add dependencies:
- Add the new dependency in a new line to `requirements.in`
- (while in the virtualenv) Run `pip-compile requirements.in`
- Rerun `pip install -r requirements.txt`
