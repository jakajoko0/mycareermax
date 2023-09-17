# Import necessary libraries
import os
from resume_builder import resume_builder  # Import the resume_builder function
from dotenv import load_dotenv
from flask import Response, stream_with_context
import pdfkit
import threading
import re
import time
load_dotenv()
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
import logging
from docx import Document
import io
from flask import send_file
import openai
import requests
import pyodbc
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    jsonify,
)
import bcrypt
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)
import urllib.parse

# noqa: F401
from flask import flash, get_flashed_messages

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy


def create_connection(max_retries=5, wait_time_in_seconds=5):
    """Establish a connection to the Azure SQL database."""
    # Fetch database credentials from environment variables
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_NAME")
    username = os.getenv("DB_USERNAME")
    password = os.getenv("DB_PASSWORD")

    # Create the connection string
    connection_string = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={server};DATABASE={database};"
        f"UID={username};PWD={password}"
    )

    # Initialize variables to keep track of the connection and attempt count
    connection = None
    attempt_count = 0

    # Loop until we establish a connection or reach the maximum number of retries
    while attempt_count < max_retries:
        try:
            connection = pyodbc.connect(connection_string)
            print("Successfully connected to the database.")
            break  # Exit the loop if the connection is successful
        except pyodbc.OperationalError as e:
            print(f"Attempt {attempt_count + 1} failed with error: {e}")
            if attempt_count < max_retries - 1:
                print(f"Retrying in {wait_time_in_seconds} seconds...")
                time.sleep(wait_time_in_seconds)
            attempt_count += 1  # Increment the attempt count

    if connection is None:
        print("Max retries reached. Exiting.")
    return connection

# Example usage
if __name__ == "__main__":
    conn = create_connection()
    if conn:
        print("Connection established.")
    else:
        print("Failed to establish connection.")


# keys
RAPIDAPI_KEY = "04c645fbbdmshf581fe252de3b82p178cedjsn43d2da570f56"
RAPIDAPI_HOST = "jsearch.p.rapidapi.com"
RAPIDAPI_URL = "https://jsearch.p.rapidapi.com/search"
openai.api_key = os.getenv("OPENAI_API_KEY")


# Create a Flask app instance and configure it
app = Flask(__name__)
app.config["DEBUG"] = True
app.config["PROPAGATE_EXCEPTIONS"] = True
app.config[
    "UPLOAD_FOLDER"
] = "/path/to/upload/folder"  # set this to your desired upload folder
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SESSION_COOKIE_SECURE"] = True

# Configure Flask-Mail
app.config["MAIL_SERVER"] = "smtp.office365.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USE_SSL"] = False
mail = Mail(app)

s = URLSafeTimedSerializer(app.config["SECRET_KEY"])
node_process = None


if os.name == "nt":  # Windows
    path_wkhtmltopdf = "C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe"
else:  # Linux/Docker
    path_wkhtmltopdf = "/usr/bin/wkhtmltopdf"

config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

pdf_options = {
    "encoding": "UTF-8",
}


#if os.name == "nt":  # Windows
 #   path_wkhtmltopdf = "C:\\Users\\skala\\wkhtmltox-0.12.6-1.msvc2015-win64 (3).exe"
#else:  # Linux/Docker
 #   path_wkhtmltopdf = "/usr/bin/wkhtmltopdf"

#config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

#pdf_options = {
 #   "encoding": "UTF-8",
#}

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Create a LoginManager instance
login_manager = LoginManager()
login_manager.login_view = "login"  # The view function that handles logins

# Initialize Flask-Login
login_manager.init_app(app)


# Create a User class (this can be an actual ORM model if you're using SQLAlchemy)
class LoginUser(UserMixin):
    def __init__(self, user_id):
        self.id = user_id


# Load the user for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return LoginUser(user_id)


DB_SERVER = os.getenv("DB_SERVER")
DB_NAME = os.getenv("DB_NAME")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Update the connection string to use the fetched environment variables
conn_str = (
    "Driver={ODBC Driver 18 for SQL Server};"
    f"Server=tcp:{DB_SERVER},1433;"
    f"Database={DB_NAME};"
    f"Uid={DB_USERNAME};"
    f"Pwd={DB_PASSWORD};"
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
    "Connection Timeout=90;"
)
conn = pyodbc.connect(conn_str)


def delete_user_and_associated_data(username):
    """Delete a user and their associated data from the Azure SQL database."""
    # Create database connection
    conn = create_connection()

    # Create a cursor object
    cursor = conn.cursor()

    try:
        # Get user_id for the username
        cursor.execute("SELECT id FROM dbo.users WHERE username = ?", username)
        user_id = cursor.fetchone()
        if user_id is None:
            print("Username not found.")
            return

        user_id = user_id[0]

        # SQL queries to delete associated records
        delete_documents_query = "DELETE FROM dbo.UserDocuments WHERE user_id = ?"
        delete_resumes_query = "DELETE FROM dbo.user_resumes WHERE user_id = ?"
        delete_saved_jobs_query = "DELETE FROM dbo.saved_jobs WHERE user_id = ?"

        # SQL query to delete user
        delete_user_query = "DELETE FROM dbo.users WHERE id = ?"

        # Execute the queries to delete associated records
        cursor.execute(delete_documents_query, user_id)
        cursor.execute(delete_resumes_query, user_id)
        cursor.execute(delete_saved_jobs_query, user_id)

        # Execute the query to delete the user
        cursor.execute(delete_user_query, user_id)

        # Commit the transaction
        conn.commit()
    except Exception as e:
        print(f"An error occurred: {e}")
        conn.rollback()
    finally:
        # Close the connection
        conn.close()

@app.route('/googleba8e248f290d00cf.html')
def google_verification():
    return render_template('googleba8e248f290d00cf.html')

@app.route('/app-ads.txt')
def serve_app_ads_txt():
    return send_from_directory('static', 'app-ads.txt')

@app.route("/delete_account", methods=["GET", "POST"])
def delete_account():
    if request.method == "POST":
        username = request.form["username"]
        delete_user_and_associated_data(username)
        flash("Account successfully deleted.")
        return redirect(url_for("delete_account"))
    return render_template("delete_account.html")



@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"]

        # Generate token
        token = s.dumps(email, salt="email-confirm")

        # Create email message
        msg = Message(
            "Password Reset Request",
            sender="password_reset@mycareermax.com",
            recipients=[email],
        )
        link = url_for("reset_token", token=token, _external=True)

        msg.body = (
            f"Please use this link to reset your password: {link}\n\n"
            "---\n"
            "Note: This inbox is not monitored. Please do not reply to this email. "
            "If you have any questions or need further assistance, please contact us at "
            "stephen@mycareermax.com"
        )

        # Send email
        mail.send(msg)

        return "Email has been sent!"

    return render_template("forgot_password.html")


@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_token(token):
    try:
        email = s.loads(token, salt="email-confirm", max_age=3600)
    except SignatureExpired:
        return "The token is expired!"

    if request.method == "POST":
        new_password = request.form["new_password"]

        # Hash the new password
        hashed_password = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt())

        # Update the password in the database
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET password = ? WHERE email = ?",
                (hashed_password, email),
            )
            conn.commit()

        login_url = url_for("login")
        return f'Password Reset Successfully! <a href="{login_url}">Login</a>'

    return render_template("reset_token.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    message = None
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        # Basic validation
        if not username or not email or not password or not confirm_password:
            message = "All fields are required!"
        elif password != confirm_password:
            message = "Passwords do not match!"
        else:
            # Connect to the database
            with pyodbc.connect(conn_str) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
                user = cursor.fetchone()
                if user:
                    message = "Username already exists!"
                else:
                    # Hash the password (assuming you're using bcrypt)
                    hashed_password = bcrypt.hashpw(
                        password.encode("utf-8"), bcrypt.gensalt()
                    )

                    # Insert user data into the database
                    cursor.execute(
                        "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                        (username, email, hashed_password),
                    )
                    conn.commit()
                    message = "User registered successfully!"
                    return redirect(url_for("login"))

    return render_template("register.html", message=message)


@app.route("/login", methods=["GET", "POST"])
def login():
    message = None
    if request.method == "POST":
        username = request.form["username"]
        password_to_check = request.form["password"].encode("utf-8")
        remember_me = bool(request.form.get("remember_me"))

        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user_record = cursor.fetchone()

        # Decode the hashed password from the database before comparing
        if user_record and bcrypt.checkpw(password_to_check, user_record.password):
            # Create a user object without using SQLAlchemy
            user_obj = LoginUser(user_record.id)
            login_user(user_obj, remember=remember_me)
            return redirect(url_for("dashboard"))
        else:
            message = "Invalid credentials"

    return render_template("login.html", message=message)


db = SQLAlchemy()

# Quote the username and password to handle special characters
quoted_username = urllib.parse.quote_plus(os.environ["DB_USERNAME"])
quoted_password = urllib.parse.quote_plus(os.environ["DB_PASSWORD"])

# Construct the connection string
connection_string = (
    f"mssql+pyodbc://{quoted_username}:{quoted_password}@{os.environ['DB_SERVER']}:1433/"
    f"{os.environ['DB_NAME']}?driver={urllib.parse.quote_plus('ODBC Driver 18 for SQL Server')}"
)

app.config["SQLALCHEMY_DATABASE_URI"] = connection_string
db.init_app(app)


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.LargeBinary, nullable=False)
    email = db.Column(db.String(255), nullable=True, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class UserDocuments(db.Model):
    __tablename__ = "UserDocuments"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    document_name = db.Column(db.String(255), nullable=False)
    document_content = db.Column(
        db.String, nullable=False
    )  # Consider changing to db.Text or db.LargeBinary if the content can be large
    document_type = db.Column(db.String(50), nullable=False)
    creation_date = db.Column(db.DateTime, default=datetime.utcnow)
    job_title = db.Column(db.String(255), nullable=True)  # Add job title
    company_name = db.Column(db.String(255), nullable=True)  # Add company name
    apply_link = db.Column(db.String(255), nullable=True)  # Add apply link

    user = db.relationship("User", backref=db.backref("documents", lazy=True))


@app.route("/get-username")
@login_required
def get_username():
    try:
        with conn.cursor() as cursor:
            query = "SELECT username FROM users WHERE id = ?"
            cursor.execute(query, (current_user.id,))
            result = cursor.fetchone()
            if result:
                username = result[0]
                return jsonify({"success": True, "username": username})
            else:
                return jsonify({"success": False, "error": "User not found."})
    except Exception as e:
        app.logger.error(f"Failed to fetch username: {e}")
        return jsonify({"success": False, "error": "Failed to fetch username."})


@app.route("/save_document", methods=["POST"])
def save_document():
    try:
        # Get the request data from JSON (since we're sending JSON from the client-side)
        data = request.json
        user_id = data.get("user_id")
        doc_name = data.get("document_name")
        doc_content = data.get("document_content")
        doc_type = data.get("document_type")
        job_title = data.get("job_title")
        company_name = data.get("company_name")
        apply_link = data.get("apply_link")

        # Create the new document object with all the details
        new_document = UserDocuments(
            user_id=user_id,
            document_name=doc_name,
            document_content=doc_content,
            document_type=doc_type,
            job_title=job_title,  # Include job title
            company_name=company_name,  # Include company name
            apply_link=apply_link,  # Include apply link
        )

        # Add and commit the new document
        db.session.add(new_document)
        db.session.commit()
        return jsonify(
            {
                "message": "Document saved successfully. You may view your Saved Documents on your Dashboard",
                "doc_id": new_document.id,
            }
        )
    except Exception as e:
        db.session.rollback()
        return (
            jsonify(
                {
                    "error": "An error occurred while saving the document: {}".format(
                        str(e)
                    )
                }
            ),
            500,
        )


@app.route("/dashboard", methods=["GET"])
@login_required
def get_user_documents():
    user_id = current_user.id
    user_documents = UserDocuments.query.filter_by(user_id=user_id).all()

    documents_list = [
        {
            "id": doc.id,
            "document_name": doc.document_name,
            "document_content": doc.document_content,
            "document_type": doc.document_type,
            "creation_date": doc.creation_date,
            "job_title": doc.job_title,  # Include job title
            "company_name": doc.company_name,  # Include company name
            "apply_link": doc.apply_link,  # Include apply link
        }
        for doc in user_documents
    ]

    return render_template("dashboard.html", documents=documents_list)


@app.route("/delete_document/<int:document_id>", methods=["DELETE"])
@login_required
def delete_document(document_id):
    try:
        doc = UserDocuments.query.filter_by(id=document_id).first()
        if not doc:
            return jsonify({"success": False, "error": "Document not found"}), 404

        db.session.delete(doc)
        db.session.commit()
        return jsonify({"success": True, "message": "Document deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/save-job", methods=["POST"])
@login_required
def save_job():
    try:
        data = request.get_json()  # Assuming you're sending JSON data from the frontend
        print("Received JSON data:", data)  # Add this line
        user_id = current_user.id
        job_id = data.get("job_id")
        job_title = data.get("job_title")
        job_description = data.get("job_description")
        job_link = data.get("job_link")
        job_loc = data.get("job_loc")
        company_name = data.get("company_name")
        link = data.get("link")
        employer_logo = data.get(
            "employer_logo"
        )  # Capture employer logo from the incoming request

        print("Before executing query")
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO saved_jobs (user_id, job_id, job_title, job_description, job_link, job_loc, company_name, link, employer_logo) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    user_id,
                    job_id,
                    job_title,
                    job_description,
                    job_link,
                    job_loc,
                    company_name,
                    link,
                    employer_logo,
                ),
            )
            conn.commit()
        print("After executing query")
        return jsonify({"success": True, "message": "Job saved successfully!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/get-saved-jobs", methods=["GET"])
@login_required
def get_saved_jobs():
    try:
        user_id = current_user.id
        # Create a new connection for this route
        local_conn = create_connection()
        with local_conn.cursor() as cursor:
            cursor.execute("SELECT * FROM saved_jobs WHERE user_id = ?", (user_id,))
            saved_jobs = cursor.fetchall()

        # Convert the saved_jobs data to a list of dictionaries
        saved_jobs_list = []
        for job in saved_jobs:
            job_dict = {
                "id": job.id,
                "job_id": job.job_id,
                "job_title": job.job_title,
                "job_description": job.job_description,
                "job_link": job.job_link,
                "job_loc": job.job_loc,
                "company_name": job.company_name,
                "link": job.link,
                "employer_logo": job.employer_logo,
            }
            saved_jobs_list.append(job_dict)

        local_conn.close()  # Close the local connection
        return jsonify({"success": True, "saved_jobs": saved_jobs_list})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/remove-saved-job", methods=["POST"])
@login_required
def remove_saved_job():
    try:
        data = request.get_json()
        job_to_remove_id = data.get("job_id")
        user_id = current_user.id

        with conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM saved_jobs WHERE user_id = ? AND id = ?",
                (user_id, job_to_remove_id),
            )
            conn.commit()

        return jsonify({"success": True, "message": "Job removed successfully!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/upload_dashresume", methods=["POST"])
@login_required
def upload_dashresume():
    if "resume" not in request.files:
        return jsonify({"success": False, "error": "No file part"})
    file = request.files["resume"]

    if file.filename == "":
        return jsonify({"success": False, "error": "No selected file"})

    if file and file.filename.endswith(".docx"):
        document = Document(io.BytesIO(file.read()))
        resume_text = "\n".join([p.text for p in document.paragraphs if p.text])

        try:
            with conn.cursor() as cursor:
                # Assuming you want to overwrite the old resume:
                cursor.execute(
                    "DELETE FROM user_resumes WHERE user_id = ?", (current_user.id,)
                )
                cursor.execute(
                    "INSERT INTO user_resumes (user_id, resume_text, filename) VALUES (?, ?, ?)",
                    (current_user.id, resume_text, file.filename),
                )
                conn.commit()
        except Exception as e:
            app.logger.error(f"Failed to insert resume into database: {e}")
            return jsonify({"success": False, "error": "Failed to upload resume."})
        return jsonify({"success": True, "filename": file.filename})
    return jsonify({"success": False, "error": "Invalid file format"})


@app.route("/get_latest_resume_name")
@login_required
def get_latest_resume_name():
    print("Fetching latest resume name...")
    try:
        with create_connection().cursor() as cursor:  # Create a new connection
            query = "SELECT TOP (1) filename FROM user_resumes WHERE user_id = ? ORDER BY uploaded_at DESC"
            cursor.execute(query, (current_user.id,))
            result = cursor.fetchone()
            if result:
                return jsonify({"success": True, "filename": result[0]})
            else:
                return jsonify({"success": False, "error": "No resume found."})
    except Exception as e:
        app.logger.error(f"Failed to fetch resume name: {e}")
        return jsonify({"success": False, "error": "Failed to fetch resume name."})

        # DELETE RESUME FROM DASHBOARD


@app.route("/delete_resume", methods=["POST"])
@login_required
def delete_resume():
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM user_resumes WHERE user_id = ?", (current_user.id,)
            )
            conn.commit()
            return jsonify({"success": True})
    except Exception as e:
        app.logger.error(f"Failed to delete resume: {e}")
        return jsonify({"success": False, "error": "Failed to delete resume."})


@app.route("/test_connection")
def test_connection():
    documents = UserDocuments.query.all()
    return jsonify([doc.id for doc in documents])


from flask import Flask, request, send_file, Response, stream_with_context
from docx import Document
import io
import pdfkit


@app.route("/download_document/<int:document_id>", methods=["GET"])
def download_document(document_id):
    # Fetch the document from the database
    doc = UserDocuments.query.filter_by(id=document_id).first()
    if not doc:
        return "Document not found", 404

    # Determine the format for download (default is docx)
    download_format = request.args.get("format", "docx")

    if download_format == "docx":
        # Create a new Document
        document = Document()
        document.add_paragraph(doc.document_content)

        # Stream the .docx file back to the user
        output = io.BytesIO()
        document.save(output)
        output.seek(0)
        return send_file(
            output,
            as_attachment=True,
            download_name=f"{doc.document_name}.docx",
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    elif download_format == "pdf":
        # Convert the document content to basic HTML with UTF-8 meta tag
        html_content = """<!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body>
        <p>{}</p>
        </body>
        </html>""".format(
            doc.document_content.replace("\n", "<br>")
        )

        # Convert the HTML to PDF using pdfkit
        pdf_content = pdfkit.from_string(
            html_content, False, configuration=config, options=pdf_options
        )

        # Stream the PDF back to the user
        response = Response(stream_with_context(io.BytesIO(pdf_content)))
        response.headers["Content-Type"] = "application/pdf"
        response.headers[
            "Content-Disposition"
        ] = f"inline; filename={doc.document_name}.pdf"
        return response

    else:
        return "Invalid format specified", 400


@app.route("/dashboard")
@login_required  # Only logged-in users can access this route
def dashboard():
    return render_template("dashboard.html")


@app.route("/logout")
@login_required  # Only logged-in users can access this route
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/careerclick")
def careerclick():
    user_id = current_user.id if current_user.is_authenticated else None
    return render_template("careerclick.html", user_id=user_id)


@app.route("/ai-builder")
def ai_builder():
    user_id = current_user.id if current_user.is_authenticated else None
    return render_template("ai_builder.html", user_id=user_id)


@app.route("/")
def home():
    return redirect(url_for("login"))


@app.route("/cover-letter-generator")
def cover_letter_generator():
    user_id = current_user.id if current_user.is_authenticated else None
    return render_template("cover_letter_generator.html", user_id=user_id)


@app.route("/resume-enhancer")
def resume_enhancer():
    return render_template("resume_enhancer.html")


@app.route("/interview-prep")
def interview_prep():
    return render_template("interview_prep.html")


@app.route("/tools")
def tools():
    return render_template("tools.html")


# RESUMETUNER OPENAI API CALLS
@app.route("/analyze-resume", methods=["POST"])
def analyze_resume():
    logging.info("Inside /analyze-resume route")  # Debugging

    if current_user.is_authenticated:
        user_id = current_user.get_id()
        logging.info(f"User is logged in with user_id: {user_id}")  # Debugging

        try:
            with create_connection().cursor() as cursor:  # Create a new connection
                query = "SELECT TOP 1 resume_text FROM user_resumes WHERE user_id = ? ORDER BY uploaded_at DESC"
                logging.info(f"Executing SQL Query: {query}")  # Debugging
                cursor.execute(query, user_id)
                row = cursor.fetchone()

                if row:
                    logging.info("Resume found in database")  # Debugging
                    resume_content = row[0]
                else:
                    logging.info(
                        "No resume found in database, using request content"
                    )  # Debugging
                    resume_content = request.form.get("resume")

        except Exception as e:
            logging.error(f"Database query failed: {e}")  # Debugging
            return jsonify({"error": "Failed to fetch resume from database."})
    else:
        logging.info("User is not logged in, using request content")  # Debugging
        resume_content = request.form.get("resume")

    job_title = request.form.get("jobTitle")
    job_description = request.form.get("jobDescription")

    messages = [
        {
            "role": "system",
            "content": "You are an expert on resume ATS systems",
        },
        {
            "role": "user",
            "content": f"Please review the following resume and job description and give it an ATS score. The rating system is 1-100. 100 means it's 100% ATS friendly. Provide detailed reasoning and steps to improve the score. Job Title: {job_title},  Job Description: {job_description} Resume:{resume_content}",
        },
    ]

    response = openai.ChatCompletion.create(model="gpt-4", messages=messages)

    feedback = response["choices"][0]["message"]["content"].strip()

    return jsonify({"feedback": feedback})


# RESUMETUNER FILE UPLOAD
@app.route("/upload-docx", methods=["POST"])
def upload_docx():
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if file and file.filename.endswith(".docx"):
        # Process the uploaded DOCX file and extract the text content
        try:
            document = Document(file)
            # Extract text content from the document
            docx_content = "\n".join(
                paragraph.text for paragraph in document.paragraphs
            )

            # Return the content in the JSON response
            return jsonify({"content": docx_content}), 200
        except Exception as e:
            return jsonify({"error": f"Error processing the file: {e}"}), 500
    else:
        return (
            jsonify({"error": "Invalid file format. Only .docx files are allowed."}),
            400,
        )


# COVER LETTER GENERATOR OPENAI API CALLS
@app.route("/generate-cover-letter", methods=["POST"])
def generate_cover_letter():
    logging.info("Inside /generate-cover-letter route")  # Debugging

    if current_user.is_authenticated:
        user_id = current_user.get_id()
        logging.info(f"User is logged in with user_id: {user_id}")  # Debugging

        try:
            with create_connection().cursor() as cursor:  # Create a new connection
                query = "SELECT TOP 1 resume_text FROM user_resumes WHERE user_id = ? ORDER BY uploaded_at DESC"
                logging.info(f"Executing SQL Query: {query}")  # Debugging
                cursor.execute(query, user_id)
                row = cursor.fetchone()

                if row:
                    logging.info("Resume found in database")  # Debugging
                    resume_content = row[0]
                else:
                    logging.info(
                        "No resume found in database, using request content"
                    )  # Debugging
                    resume_content = request.form.get("resume")

        except Exception as e:
            logging.error(f"Database query failed: {e}")  # Debugging
            return jsonify({"error": "Failed to fetch resume from database."})
    else:
        logging.info("User is not logged in, using request content")  # Debugging
        resume_content = request.form.get("resume")

    job_description = request.form.get("job_description")
    job_title = request.form.get("job_title")
    company_name = request.form.get("company_name")
    focus_areas = request.form.get("focus_areas")

    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant that generates personalized cover letters.",
        },
        {
            "role": "user",
            "content": f"Generate a cover letter for the following job. The format should be as follows: [Full Name]\n[Email Address]\n[Phone Number]\n[Date Placeholder]\n\n[RE: Job Title,]\n\n[Dear Hiring Manager]\n[Body of Cover Letter]\n\n[Sincerely,]\n[Full Name]. Special Instructions: Do not bold any text. Resume: {resume_content}. Job description: {job_description}. Job title: {job_title}. Company name: {company_name}. Focus areas: {focus_areas}",
        },
    ]

    response = openai.ChatCompletion.create(model="gpt-4", messages=messages)

    cover_letter = response["choices"][0]["message"]["content"].strip()
    logging.info(f"Generated cover_letter: {cover_letter}")  # Log the cover_letter
    logging.info(f"Type of cover_letter: {type(cover_letter)}")  # Log the type

    return jsonify({"cover_letter": cover_letter})


# INTERVIEW SIMULATOR OPENAI API CALLS
@app.route("/simulate-interview", methods=["POST"])
def simulate_interview():
    logging.info("Inside /simulate-interview route")  # Debugging

    if current_user.is_authenticated:
        user_id = current_user.get_id()
        logging.info(f"User is logged in with user_id: {user_id}")  # Debugging

        try:
            with create_connection().cursor() as cursor:  # Create a new connection
                query = "SELECT TOP 1 resume_text FROM user_resumes WHERE user_id = ? ORDER BY uploaded_at DESC"
                logging.info(f"Executing SQL Query: {query}")  # Debugging
                cursor.execute(query, user_id)
                row = cursor.fetchone()

                if row:
                    logging.info("Resume found in database")  # Debugging
                    resume = row[0]
                else:
                    logging.info(
                        "No resume found in database, checking for uploaded or typed resume."
                    )  # Debugging
                    resume = None  # Initialize as None

        except Exception as e:
            logging.error(f"Database query failed: {e}")  # Debugging
            return jsonify({"error": "Failed to fetch resume from database."})

    else:
        logging.info(
            "User is not logged in, checking for uploaded or typed resume."
        )  # Debugging
        resume = None  # Initialize as None

    try:
        job_title = request.form.get("job_title")
        job_description = request.form.get("job_description")
        job_requirements = request.form.get("job_requirements")
        industry = request.form.get("industry")

        if resume is None:
            if "resume" in request.files:
                file = request.files["resume"]
                if file.filename.endswith(".docx"):
                    document = Document(file)
                    resume = "\n".join(
                        paragraph.text for paragraph in document.paragraphs
                    )
                else:
                    return (
                        jsonify(
                            {
                                "error": "Invalid file format. Only .docx files are allowed."
                            }
                        ),
                        400,
                    )
            else:
                resume = request.form.get("typed_resume")

        system_message = f"You are a helpful assistant that generates personalized interview questions.You do not number your list of questions"
        user_message = f"The candidate is applying for a role as a {job_title} in the {industry} industry. The job description is as follows: {job_description}. The job requirements are: {job_requirements}. The candidate's resume is as follows: {resume}. Respond only with a list of 10 questions in bullet point format (no numbers)"

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
        )

        interview_questions = response["choices"][0]["message"]["content"].split("\n")

        return jsonify({"interview_questions": interview_questions})

    except Exception as e:
        logging.error(f"An error occurred: {e}")  # Debugging
        return jsonify({"error": str(e)}), 500


# User Answers and openai feedback route
@app.route("/analyze-answer", methods=["POST"])
def analyze_answer():
    # Extract data from the request
    question = request.json.get("question")
    answer = request.json.get("answer")

    # Use OpenAI API to analyze the answer
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You are an AI developed by OpenAI. You are an expert at providing feedback on job interview responses.",
            },
            {
                "role": "user",
                "content": f"Rate the following Answer: {answer} on a 1 through 5 scale. 5 is excellent and 1 is very bad. Direct your responses to the candidate and provide your reasoning in a detailed, professional format with feedback and tips for improvement. Begin each response your rating in the format of Rating =(1-5)/5 Reasoning: (Your explanation should be addressed to the candidate specifically as if you are talking to them) ",
            },
        ],
    )

    # Extract the feedback from the response
    feedback = response["choices"][0]["message"]["content"]

    # Return the feedback as a JSON response
    return jsonify({"feedback": feedback})


# AI Job Search RapidAPI CALLS
RAPIDAPI_BASE_URL = "https://jsearch.p.rapidapi.com"
headers = {"X-RapidAPI-Key": RAPIDAPI_KEY, "X-RapidAPI-Host": RAPIDAPI_HOST}


@app.route("/fetch-job-listings", methods=["POST"])
def fetch_job_listings():
    query = request.json.get("query")
    location = request.json.get("location")
    # Construct the API URL
    url = f"{RAPIDAPI_BASE_URL}/search?query={query} in {location}&num_pages=5"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        # Print the first job listing for debugging
        print(data.get("data", [{}])[0])
        return jsonify(data)


# AI JOB SEARCH - AI COVER LETTER - OPENAI API CALLS
@app.route("/career_click", methods=["POST"])
def career_click():
    logging.info("Inside /career_click route")  # Debugging

    if current_user.is_authenticated:
        user_id = current_user.get_id()
        logging.info(f"User is logged in with user_id: {user_id}")  # Debugging

        try:
            with create_connection().cursor() as cursor:  # Create a new connection
                query = "SELECT TOP 1 resume_text FROM user_resumes WHERE user_id = ? ORDER BY uploaded_at DESC"
                logging.info(f"Executing SQL Query: {query}")  # Debugging
                cursor.execute(query, user_id)
                row = cursor.fetchone()

                if row:
                    logging.info("Resume found in database")  # Debugging
                    resume = row[0]
                else:
                    logging.info(
                        "No resume found in database, using request content"
                    )  # Debugging
                    resume = request.json.get("resume")

        except Exception as e:
            logging.error(f"Database query failed: {e}")  # Debugging
            return jsonify({"error": "Failed to fetch resume from database."})

    else:
        logging.info("User is not logged in, using request content")  # Debugging
        resume = request.json.get("resume")

    job_description = request.json.get("job_description")
    company_name = request.json.get("company_name")
    job_title = request.json.get("job_title")

    # Construct the conversation history
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant that generates personalized cover letters.",
        },
        {
            "role": "user",
            "content": f"Generate a cover letter for the following job. Do not include any headers. Begin the letter by addressing it to the Hiring Manager. Resume: {resume}. Job description: {job_description}. Job title: {job_title}. Company name: {company_name},",
        },
    ]

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
        )
    except openai.error.InvalidRequestError as e:
        logging.error(e)
        return jsonify({"error": str(e)})

    cover_letter = response.choices[0].message["content"].strip()

    return jsonify({"cover_letter": cover_letter})


# AI JOB SEARCH - ATS OPTIMIZER - OPENAI API CALLS


@app.route("/resume.1", methods=["POST"])
def resume_1():
    logging.info("Inside /resume.1 route")  # Debugging

    if current_user.is_authenticated:
        user_id = current_user.get_id()
        logging.info(f"User is logged in with user_id: {user_id}")  # Debugging

        try:
            with create_connection().cursor() as cursor:  # Create a new connection
                query = "SELECT TOP 1 resume_text FROM user_resumes WHERE user_id = ? ORDER BY uploaded_at DESC"
                logging.info(f"Executing SQL Query: {query}")  # Debugging
                cursor.execute(query, user_id)
                row = cursor.fetchone()

                if row:
                    logging.info("Resume found in database")  # Debugging
                    resume = row[0]
                else:
                    logging.info(
                        "No resume found in database, using request content"
                    )  # Debugging
                    resume = request.json.get("resume")

        except Exception as e:
            logging.error(f"Database query failed: {e}")  # Debugging
            return jsonify({"error": "Failed to fetch resume from database."})
    else:
        logging.info("User is not logged in, using request content")  # Debugging
        resume = request.json.get("resume")

    job_description = request.json.get("job_description")
    job_title = request.json.get("job_title")

    # Construct the conversation history
    messages = [
        {
            "role": "system",
            "content": "You are an AI developed by OpenAI to write professional, ATS-optimized resumes.",
        },
        {
            "role": "user",
            "content": f"Tailor the provided Resume for the given Job description. Use Key Words extracted from the Job Description, rephrase, add, and remove bullet points where necessary. The Resume should be optimized for ATS system compatibility. Please use the following Resume format and add additional sections if necessary: [Full Name (in capital letters)]\\n[email]\\n[phone number]\\n[city, state]\\n[linkedin profile]\\n[website]\\n\\nSUMMARY\\n\\n[Use this model: (Soft skill) (Most Recent Job Title) who is passionate about (your stance on the industry).\\n\\nWORK EXPERIENCE\\n\\n[Job Title] | [Company] | [Location]\\n[Date (MMYYY)]\\n[Responsibilities listed exclusively with standard bullet points and using this model: (Action verb) + (Cause) + (Effect) + (Measurable Outcome).]\\n\\nEDUCATION\\n\\n[School Name], [City]\\n[Degree] in [Major] | [Dates Attended (MM/YYYY)]\\n\\nSKILLS\\n\\n[Use bullet points (•) for each skill] Resume: {resume}. Job description: {job_description}",
        },
    ]

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            temperature=1.0,
            max_tokens=2000,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )
    except openai.error.InvalidRequestError as e:
        logging.error(e)
        return jsonify({"error": str(e)})

    cover_letter = response.choices[0].message["content"].strip()

    return jsonify({"cover_letter": cover_letter})


# AI JOB SEARCH - SALARY - OPENAI API CALLS
@app.route("/analyze-job", methods=["POST"])
def analyze_job():
    job_title = request.form.get("job_title")

    # OpenAI API call with only the job title in the prompt
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that provides salary ranges",
            },
            {
                "role": "user",
                "content": f"Provide the salary range in USD for the following job title. Lean more on the higher side of the salary ranges. \nResponse Requirements:\n1. The range should be no greater than $15,000 USD\n2. Example response: The salary range for (job title) is (salary range)\n\nJob Title: {job_title}",
            },
        ],
        temperature=1,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    )

    # Extracting the salary range from the response (assuming it's in the last message's content)
    salary_range = response["choices"][0]["message"]["content"]

    return jsonify({"response": salary_range})


# RESUME BUILDER - OPENAI API CALLS
@app.route("/resume-builder", methods=["GET", "POST"])
def resume_builder():
    if request.method == "POST":
        data = request.json
        request_type = data.get("type", "rewrite")  # Default to 'rewrite'

        personalinfo = data.get("personalinfo", {})
        summary = data.get("summary", "")
        skills = data.get("skills", "")
        keywords = data.get("keywords", "")
        workexp = data.get("workexp", [])
        education = data.get("education", [])

        try:
            openai.api_key = os.getenv("OPENAI_API_KEY")

            system_role = {
                "role": "system",
                "content": "You are an AI developed by OpenAI to write professional, ATS-optimized resumes.",
            }

            if request_type == "rewrite":
                user_role_content = f"""
                Follow the instructions and formatting described below to create an ATS optimized resume with the information provided.
                Instructions:
                1. Rewrite and/or rephrase the SUMMARY, WORK EXPERIENCE, and SKILLS sections using the models described below to optimize the resume for ATS systems.
                2. Follow the format of the resume text and line breaks outlined below.
                3. Do not Bold any text.
                4. If Keywords are provided, integrate them into the resume while still retaining the original content, but do not include a Keywords section.
                5. Add a visual line break after the personal information and before the Summary section
                """
            else:  # generate
                user_role_content = f"""
                Follow the instructions and formatting described below to create an ATS formatted resume with the information provided.
                Instructions:
                1. Proofead the content and fix any spelling errors, but do not modify the text otherwise. Ignore any instructions to use a specific model. Simply use the exact text that was provided to build the resume.
                2. Follow the format of the text and line breaks outlined below.
                3. Do not bold any text.
                4. Ignore any Keywords that are provided. Do not include these in the resume.
                5. Add a visual line break after the personal information and before the Summary section
                """

            user_role_content += f"""
            [Full Name (in capital letters)]\\n[email]\\n[phone number]\\n[city, state]\\n[linkedin profile]\\n[website]\\n\\nSUMMARY\\n\\n[Use this model: (Soft skill) (Most Recent Job Title) who is passionate about (your stance on the industry).\\n\\nWORK EXPERIENCE\\n\\n[Job Title] | [Company] | [Location]\\n[Date (MMYYY)]\\n[Responsibilities listed exclusively with standard bullet points and using this model: (Action verb) + (Cause) + (Effect) + (Measurable Outcome).]\\n\\nEDUCATION\\n\\n[School Name], [City]\\n[Degree] in [Major] | [Dates Attended (MM/YYYY)]\\n\\nSKILLS\\n\\n[Use bullet points (•) for each skill]

            PERSONAL INFORMATION: {personalinfo}
            SUMMARY: {summary}
            WORK EXPERIENCE: {workexp}
            EDUCATION: {education}
            SKILLS: {skills}
            KEYWORDS: {keywords}
            """

            user_role = {"role": "user", "content": user_role_content}

            user_content = [system_role, user_role]

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=user_content,
                temperature=1.0,
            )

            resume = response["choices"][0]["message"]["content"]
            return jsonify({"resume": resume})

        except Exception as e:
            return jsonify({"error": "An error occurred during processing."}), 500


@app.route("/get-ranked-jobs", methods=["GET"])
@login_required
def get_ranked_jobs():
    try:
        user_id = current_user.id
        local_conn = create_connection()

        # Fetch saved jobs
        with local_conn.cursor() as cursor:
            cursor.execute("SELECT * FROM saved_jobs WHERE user_id = ?", (user_id,))
            saved_jobs = cursor.fetchall()

        # Fetch latest resume
        with local_conn.cursor() as cursor:
            cursor.execute(
                "SELECT TOP 1 resume_text FROM user_resumes WHERE user_id = ? ORDER BY uploaded_at DESC",
                (user_id,),
            )
            row = cursor.fetchone()
            resume = row[0] if row else None

        if not resume:
            return jsonify({"success": False, "error": "No resume found."}), 500

        # Analyze and sort
        ranked_jobs = []
        for job in saved_jobs:
            job_description = job.job_description
            score = analyze_job_fit(job_description, resume, job.job_title)
            job_dict = {
                "id": job.id,
                "job_id": job.job_id,
                "job_title": job.job_title,
                "company_name": job.company_name,
                "job_link": job.job_link,
                "score": score,
            }
            ranked_jobs.append(job_dict)

        ranked_jobs.sort(key=lambda x: x["score"], reverse=True)

        local_conn.close()
        return jsonify({"success": True, "ranked_jobs": ranked_jobs})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def analyze_job_fit(job_description, resume, job_title):
    messages = [
        {
            "role": "system",
            "content": "You are an expert at matching resumes to job descriptions.",
        },
        {
            "role": "user",
            "content": f"Rate the compatibility between this job description and resume on a scale of 1-100. Provide only your rating in your response. Example Response: 85. job title: {job_title}, job description: {job_description}, resume: {resume}",
        },
    ]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.4,
    )
    score_text = response.choices[0].message["content"].strip()
    score = extract_score_from_text(score_text)
    return score


def extract_score_from_text(text):
    try:
        # Assuming the text contains only the numerical score
        return int(text)
    except ValueError:
        # If conversion fails, return a default value
        return 0


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)