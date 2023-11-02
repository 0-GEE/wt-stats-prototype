import os
from flask import Flask, session, request, abort, send_from_directory, render_template
from functools import wraps
from secrets import token_urlsafe
from dotenv import load_dotenv, find_dotenv
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta


load_dotenv(find_dotenv())

APP_SECRET_KEY = os.getenv('APP_SECRET_KEY')

COL_TIME = "time_elapsed"
COL_IAS = "IAS  km/h"
COL_ALT = "H  m"

GET_FILE_EXT_ALLOWLIST = [
    "png",
    "jpg",
    "jpeg"
]


app = Flask(__name__)

app.secret_key = APP_SECRET_KEY
app.config['UPLOAD_FOLDER'] = "files"


def get_column_by_header(filename, col_name):
    df = pd.read_csv(filename)
    return df[col_name].tolist()


def iso_to_filename(fname: str):
    return fname.replace(":", "_")

def filename_to_iso(fname: str):
    return fname.replace("_", ":")


def session_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            if session["stopped"]:
                abort(401)
            
            start_time = datetime.fromisoformat(session["start_time"])
            curr_time = datetime.utcnow()

            if start_time > curr_time:
                abort(401)
        except:
            abort(400)
        return f(*args, **kwargs)
    return decorated_function

@app.route("/", methods = ['GET'])
def index():
    return render_template("index.html")


@app.route("/api/data", methods = ['POST'])
@session_required
def receive_data():
    if not request.is_json:
        abort(400)

    data = request.get_json()
    fname = os.path.join(app.config['UPLOAD_FOLDER'], iso_to_filename(session["start_time"]) + ".csv")

    curr_time = datetime.utcnow()
    start_time = datetime.fromisoformat(session["start_time"])
    delta_t = (curr_time - start_time) / timedelta(minutes=1)

    try:
        df = pd.DataFrame(

            {
                "time_elapsed": delta_t, "H  m": float(data["H, m"]), "IAS  km/h": float(data["IAS, km/h"])
            },
            index=[0]
        )
        df.to_csv(fname, mode='a', header=False, index=False)
    except Exception as e:
        print(e)
        return {"success": False}
    
    return {"success": True}


@app.route("/api/start", methods = ['POST'])
def start_session():
    try:
        if not session["stopped"]:
            return {"success": False, "reason": "already in active session"}
    except KeyError:
        pass

    curr_time = datetime.utcnow()

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], iso_to_filename(curr_time.isoformat()) + ".csv")

    with open(filepath, 'w') as f:
        f.writelines([f"{COL_TIME},{COL_ALT},{COL_IAS}\n"])

    session["start_time"] = curr_time.isoformat()
    session["stopped"] = False

    return {"success": True}



@app.route("/api/stop", methods = ['POST'])
@session_required
def stop_session():
    session["stopped"] = True

    csv_path = os.path.join(app.config['UPLOAD_FOLDER'], iso_to_filename(session["start_time"]) + ".csv")

    alt_col = get_column_by_header(csv_path, COL_ALT)
    time_col = get_column_by_header(csv_path, COL_TIME)
    ias_col = get_column_by_header(csv_path, COL_IAS)

    alt_figure_filename = os.path.join(app.config['UPLOAD_FOLDER'], iso_to_filename(session["start_time"]) + "_alt.jpg")

    plt.plot(time_col, alt_col)
    plt.title("Altitude vs. Time")
    plt.ylabel("Altitude (m)")
    plt.xlabel("Time Elapsed (min)")
    plt.savefig(alt_figure_filename)

    ias_figure_filename = os.path.join(app.config['UPLOAD_FOLDER'], iso_to_filename(session["start_time"]) + "_ias.jpg")

    plt.clf()

    plt.plot(time_col, ias_col)
    plt.title("IAS vs. Time")
    plt.ylabel("IAS (km/h)")
    plt.xlabel("Time Elapsed (min)")
    plt.savefig(ias_figure_filename)

    return {
        "altitude_plot": f"/files/{os.path.basename(alt_figure_filename)}",
        "ias_plot": f"/files/{os.path.basename(ias_figure_filename)}"
    }



@app.route("/files/<filename>", methods = ['GET'])
def get_file(filename):
    if filename.split(".")[-1] not in GET_FILE_EXT_ALLOWLIST:
        abort(403)

    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)




if __name__ == "__main__":
    app.run("0.0.0.0", 80)

