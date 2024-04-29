# app.py

from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime
import io
import base64

app = Flask(__name__)


def create_db():
    # Create the SQLite database and tables if they don't exist
    conn = sqlite3.connect('job_applications.db')
    c = conn.cursor()

    # Create companies table
    c.execute('''CREATE TABLE IF NOT EXISTS companies (
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE
                )''')

    # Create applications table
    c.execute('''CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY,
                    company_id INTEGER,
                    job_title TEXT,
                    application_url TEXT,
                    status TEXT,
                    application_date DATE,
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )''')

    # Commit changes and close connection
    conn.commit()
    conn.close()

# Module 1: Enter Job Applications
def enter_job_application(company_name, job_title, application_url):
    conn = sqlite3.connect('job_applications.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO companies (name) VALUES (?)", (company_name,))
    application_date = datetime.today().strftime('%Y-%m-%d')
    c.execute("INSERT INTO applications (company_id, job_title, application_url, status, application_date) VALUES ((SELECT id FROM companies WHERE name=?),?,?,?,?)",
              (company_name, job_title, application_url, 'In Progress', application_date))
    conn.commit()
    conn.close()

# Module 2: Update Application Status
def update_application_status(application_id, new_status):
    conn = sqlite3.connect('job_applications.db')
    c = conn.cursor()
    c.execute("UPDATE applications SET status=? WHERE id=?", (new_status, application_id))
    conn.commit()
    conn.close()

# Module 3: Graph Application Status Over Time
# Module 3: Graph Application Status Over Time
def generate_application_data():
    conn = sqlite3.connect('job_applications.db')
    c = conn.cursor()
    c.execute("SELECT application_date, status, COUNT(*) FROM applications GROUP BY application_date, status")
    data = c.fetchall()
    
    dates = []
    counts = []
    colors = {'Accepted': 'green', 'Declined': 'red', 'In Progress': 'blue'}
    status_data = {}
    for row in data:
        date = row[0]
        status = row[1]
        count = row[2]
        if date not in status_data:
            status_data[date] = {'Accepted': 0, 'Declined': 0, 'In Progress': 0}
        status_data[date][status] = count
    
    return status_data


# Home page
@app.route('/')
def home():
    create_db()
    status_data = generate_application_data()
    return render_template('index.html', status_data=status_data)

# Flask route to render the update status page
@app.route('/update_status', methods=['GET', 'POST'])
def update_status():
    if request.method == 'POST':
        application_id = request.form['application_id']
        new_status = request.form['status']
        update_application_status(application_id, new_status)
        # return redirect(url_for('update_status'))
    
    # Fetch all companies and their applications
    conn = sqlite3.connect('job_applications.db')
    c = conn.cursor()
    c.execute("SELECT companies.name, applications.id, applications.job_title, applications.application_date, applications.status, applications.application_url FROM companies INNER JOIN applications ON companies.id = applications.company_id")
    data = c.fetchall()
    conn.close()

    # Group applications by company name
    applications_by_company = {}
    for row in data:
        company_name = row[0]
        application_info = row[1:]
        if company_name not in applications_by_company:
            applications_by_company[company_name] = []
        applications_by_company[company_name].append(application_info)
    return render_template('update_status.html', applications=applications_by_company)

# Add job application page
@app.route('/add_application', methods=['GET', 'POST'])
def add_application():
    if request.method == 'POST':
        company_name = request.form['company_name']
        job_title = request.form['job_title']
        application_url = request.form['application_url']
        enter_job_application(company_name, job_title, application_url)
        return redirect(url_for('home'))
    return render_template('add_application.html')



if __name__ == '__main__':
    app.run(debug=True)
