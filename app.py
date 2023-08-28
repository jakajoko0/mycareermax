# Import necessary libraries
import os
from dotenv import load_dotenv
from flask import Response, stream_with_context
import pdfkit

load_dotenv()
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


def create_connection():
    """Establish a connection to the Azure SQL database."""
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_NAME")
    username = os.getenv("DB_USERNAME")  # Ensure this is the correct key from .env
    password = os.getenv("DB_PASSWORD")  # Ensure this is the correct key from .env

    connection_string = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={server};DATABASE={database};"
        f"UID={username};PWD={password}"
    )
    return pyodbc.connect(connection_string)


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

if os.name == "nt":  # Windows
    path_wkhtmltopdf = "C:\\Users\\skala\\wkhtmltox-0.12.6-1.msvc2015-win64 (3).exe"
else:  # Linux/Docker
    path_wkhtmltopdf = "/usr/bin/wkhtmltopdf"

config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)


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


@app.before_request
def require_login():
    allowed_routes = [
        "login",
        "register",
    ]  # List of routes that don't require authentication

    if not current_user.is_authenticated and request.endpoint not in allowed_routes:
        return redirect(url_for("login"))


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    # Placeholder for password reset functionality
    # For now, it will just render a message
    return "Password reset functionality will be added here"


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
            # Fetch the user object using SQLAlchemy
            user_obj = User.query.filter_by(id=user_record.id).first()
            if user_obj:
                login_user(user_obj, remember=remember_me)
                return redirect(url_for("careerclick"))
            else:
                message = "User not found"
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
            {"message": "Document saved successfully", "doc_id": new_document.id}
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


@app.route("/test_connection")
def test_connection():
    documents = UserDocuments.query.all()
    return jsonify([doc.id for doc in documents])


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
        document.add_heading(doc.document_name, 0)
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
        # Convert the document content to basic HTML
        html_content = "<h1>{}</h1><p>{}</p>".format(
            doc.document_name, doc.document_content.replace("\n", "<br>")
        )

        # Convert the HTML to PDF using pdfkit
        pdf_content = pdfkit.from_string(html_content, False, configuration=config)

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


@app.route("/background-image")
def background_image():
    return render_template("background_image.html")


@app.route("/")
def home():
    return redirect(url_for("dashboard"))


@app.route("/cover-letter-generator")
def cover_letter_generator():
    return render_template("cover_letter_generator.html")


@app.route("/resume-enhancer")
def resume_enhancer():
    return render_template("resume_enhancer.html")


@app.route("/interview-prep")
def interview_prep():
    return render_template("interview_prep.html")


# RESUMETUNER OPENAI API CALLS
@app.route("/analyze-resume", methods=["POST"])
def analyze_resume():
    # Extract the content from the request
    resume_content = request.form.get("resume")
    job_title = request.form.get("jobTitle")  
    job_description = request.form.get("jobDescription")
    # Construct the messages for the OpenAI API
    messages = [
        {
            "role": "system",
            "content": "You are an expert on resume ATS systems",
        },
        {
            "role": "user",
            "content": f"Please review the following resume and job description and give it an ATS score. The rating system is 1-100. 100 means it's 100% ATS friendly. Provide detailed reasoning and steps to improve the score. Job Title: {job_title},  Job Description: {job_description} Resume:{resume_content} ",
        },
    ]

    # Send the messages to the OpenAI API
    response = openai.ChatCompletion.create(model="gpt-4", messages=messages)

    # Extract the model's reply from the response
    feedback = response["choices"][0]["message"]["content"].strip()

    # Return the feedback to the front end
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


# COVERME OPENAI API CALLS
@app.route("/generate-cover-letter", methods=["POST"])
def generate_cover_letter():
    # Extract the content from the request
    resume_content = request.form.get("resume")
    job_description = request.form.get("job_description")
    job_title = request.form.get("job_title")
    company_name = request.form.get("company_name")
    focus_areas = request.form.get("focus_areas")

    # Construct the messages for the OpenAI API
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant that generates personalized cover letters.",
        },
        {
            "role": "user",
            "content": f"Generate a cover letter for the following job. Resume: {resume_content}. Job description: {job_description}. Job title: {job_title}. Company name: {company_name}. Focus areas: {focus_areas}",
        },
    ]

    # Send the messages to the OpenAI API
    response = openai.ChatCompletion.create(model="gpt-4", messages=messages)

    # Extract the model's reply from the response
    cover_letter = response["choices"][0]["message"]["content"].strip()

    # Return the cover letter to the front end
    return jsonify({"cover_letter": cover_letter})


# INTERVIEW SIMULATOR OPENAI API CALLS
@app.route("/simulate-interview", methods=["POST"])
def simulate_interview():
    try:
        # Extract form data
        job_title = request.form.get("job_title")
        job_description = request.form.get("job_description")
        job_requirements = request.form.get("job_requirements")
        industry = request.form.get("industry")

        # If the resume was uploaded as a file
        if "resume" in request.files:
            file = request.files["resume"]
            if file.filename.endswith(".docx"):
                # Process the uploaded DOCX file and extract the text content
                document = Document(file)
                # Extract text content from the document
                resume = "\n".join(paragraph.text for paragraph in document.paragraphs)
            else:
                return (
                    jsonify(
                        {"error": "Invalid file format. Only .docx files are allowed."}
                    ),
                    400,
                )
        else:
            # If the resume was typed
            resume = request.form.get("typed_resume")

        # Define the system message for the AI
        system_message = f"You are a helpful assistant that generates personalized interview questions.You do not number your list of questions"
        # Define the user message for the AI
        user_message = f"The candidate is applying for a role as a {job_title} in the {industry} industry. The job description is as follows: {job_description}. The job requirements are: {job_requirements}. The candidate's resume is as follows: {resume}. Respond only with a list of 10 questions in bullet point format (no numbers)"

        # Use these messages to generate interview questions
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
        )

        # Extract the interview questions from the response
        interview_questions = response["choices"][0]["message"]["content"].split("\n")

        # Return the questions as a JSON response
        return jsonify({"interview_questions": interview_questions})
    except Exception as e:
        print(f"An error occurred: {e}")
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


# COVERME PRO RapidAPI CALLS
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
    # Extract the resume, job description, company name, and job title from the request
    resume = request.json.get("resume")
    job_description = request.json.get("job_description")
    company_name = request.json.get("company_name")
    job_title = request.json.get("job_title")

    # Construct the conversation history as an array of messages
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

    # Make the API call to OpenAI's GPT-3.5 model
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
    )

    # Extract the generated cover letter from the response
    cover_letter = response.choices[0].message["content"].strip()

    # Return the generated cover letter as a JSON response
    return jsonify({"cover_letter": cover_letter})


# AI JOB SEARCH - ATS OPTIMIZER - OPENAI API CALLS


@app.route("/resume.1", methods=["POST"])
def resume_1():
    # Extract the resume, job description, and job title from the request
    resume = request.json.get("resume")
    job_description = request.json.get("job_description")
    job_title = request.json.get("job_title")

    # Construct the conversation history as an array of messages
    messages = [
        {
            "role": "system",
            "content": "You are an expert at extracting keywords from job descriptions and optimizing resumes for ATS systems.",
        },
        {
            "role": "user",
            "content": f"Extract 10 keywords from the following job description and incoporate them into the resume provided. Format the resume to ATS standards by using dashes instead of bullet points. Acceptable Date Format MM/YYYY. As in, 03/2023. Resume: {resume}. Job description: {job_description}",
        },
    ]

    # Make the API call to OpenAI's GPT-4 model
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7,
            max_tokens=2000,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )
    except openai.error.InvalidRequestError as e:
        print(e)
        return jsonify({"error": str(e)})

    # Extract the generated cover letter from the response
    cover_letter = response.choices[0].message["content"].strip()

    # Return the generated cover letter as a JSON response
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
