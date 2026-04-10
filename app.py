from cs50 import SQL
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, timedelta

app = Flask(__name__)
db = SQL("sqlite:///swim.db")

@app.route("/")
def index():
    all_swimmers = db.execute("SELECT * FROM swimmers ORDER BY name ASC")
    active_swimmers = db.execute("""
        SELECT DISTINCT swimmers.id, swimmers.name
        FROM swimmers
        JOIN times_log ON swimmers.id = times_log.swimmer_id
        ORDER BY swimmers.name ASC
    """)
    return render_template("index.html", all_swimmers=all_swimmers, active_swimmers=active_swimmers)

@app.route("/add_swimmer", methods=["POST"])
def add_swimmer():
    name = request.form.get("name")
    birth_year = request.form.get("birth_year") # تعديل الاسم هنا
    if name and birth_year:
        db.execute("INSERT INTO swimmers (name, birthdate) VALUES (?, ?)", name, birth_year)
    return redirect(url_for("index"))

@app.route("/delete_swimmer/<int:swimmer_id>")
def delete_swimmer(swimmer_id):
    db.execute("DELETE FROM times_log WHERE swimmer_id = ?", swimmer_id)
    db.execute("DELETE FROM swimmers WHERE id = ?", swimmer_id)
    return redirect(url_for("index"))

@app.route("/log_time", methods=["POST"])
def log_time():
    swimmer_id = request.form.get("swimmer_id")
    distance = request.form.get("distance")
    stroke = request.form.get("stroke")
    time_seconds = request.form.get("time_seconds")
    notes = request.form.get("notes")
    if swimmer_id and distance and stroke and time_seconds:
        db.execute("INSERT INTO times_log (swimmer_id, distance, stroke, time_seconds, notes) VALUES (?, ?, ?, ?, ?)",
                   swimmer_id, distance, stroke, time_seconds, notes)
    return redirect(url_for("index"))

@app.route("/report/<int:swimmer_id>")
def report(swimmer_id):
    res = db.execute("SELECT * FROM swimmers WHERE id = ?", swimmer_id)
    if not res: return "404", 404
    swimmer = res[0]
    selected_stroke = request.args.get("stroke", "حرة")
    last_week = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    current_month = datetime.now().strftime('%m')

    weekly = db.execute("SELECT MIN(time_seconds) as best, AVG(time_seconds) as avg, COUNT(*) as count FROM times_log WHERE swimmer_id = ? AND stroke = ? AND date_recorded >= ?", swimmer_id, selected_stroke, last_week)[0]
    monthly = db.execute("SELECT MIN(time_seconds) as best, AVG(time_seconds) as avg, COUNT(*) as count FROM times_log WHERE swimmer_id = ? AND stroke = ? AND strftime('%m', date_recorded) = ?", swimmer_id, selected_stroke, current_month)[0]
    history = db.execute("SELECT * FROM times_log WHERE swimmer_id = ? AND stroke = ? ORDER BY date_recorded DESC", swimmer_id, selected_stroke)

    return render_template("report.html", swimmer=swimmer, weekly=weekly, monthly=monthly, history=history, selected_stroke=selected_stroke, swimmer_id=swimmer_id)

@app.route("/delete_log/<int:log_id>/<int:swimmer_id>")
def delete_log(log_id, swimmer_id):
    db.execute("DELETE FROM times_log WHERE id = ?", log_id)
    return redirect(url_for('report', swimmer_id=swimmer_id))

if __name__ == "__main__":
    app.run(debug=True)
