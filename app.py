# Import necessary libraries
import os
import logging
from docx import Document
import openai
import requests
from dotenv import load_dotenv
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

# noqa: F401
from flask import flash, get_flashed_messages


load_dotenv()

# keys
RAPIDAPI_KEY = "04c645fbbdmshf581fe252de3b82p178cedjsn43d2da570f56"
RAPIDAPI_HOST = "jsearch.p.rapidapi.com"
RAPIDAPI_URL = "https://jsearch.p.rapidapi.com/search"
openai.api_key = os.getenv("OPENAI_API_KEY")


# Create a Flask app instance and configure it
app = Flask(__name__)
app.config["DEBUG"] = True
app.config["PROPAGATE_EXCEPTIONS"] = True

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SESSION_COOKIE_SECURE"] = True


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
class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id


# Load the user for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User(user_id)


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


# Register Route
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"].encode("utf-8")  # Convert to bytes
        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())

        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                (username, email, hashed_password),
            )
            conn.commit()
            flash("User registered successfully!", "success")
            return redirect(url_for("login"))
        except pyodbc.IntegrityError:
            flash("Username or email already exists.", "danger")
            return render_template(
                "register.html"
            )  # Render the register template again

    return render_template("register.html")


# Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    message = None
    if request.method == "POST":
        username = request.form["username"]
        password_to_check = request.form["password"].encode("utf-8")

        # Convert the remember_me value to a boolean
        remember_me = bool(request.form.get("remember_me"))

        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        # Decode the hashed password from the database before comparing
        if user and bcrypt.checkpw(password_to_check, user.password):
            user_obj = User(user.id)
            login_user(user_obj, remember=remember_me)
            return redirect(url_for("dashboard"))
        else:
            message = "Invalid credentials"

    return render_template("login.html", message=message)


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
    return render_template("careerclick.html")


@app.route("/background-image")
def background_image():
    return render_template("background_image.html")


@app.route("/")
def home():
    return render_template("home.html")


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

    # Construct the messages for the OpenAI API
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant that reviews and provides feedback on resumes.",
        },
        {
            "role": "user",
            "content": f"Review and rate the following resume on a scale from 1 (lowest) to 5 (highest). Give your reasoning in a detailed analysis with tips and suggestions for improvement. Make it no more than 250 words: {resume_content}",
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
        return jsonify(response.json())
    else:
        return jsonify({"error": "Failed to fetch job listings"}), 500


# COVERME PRO - coverME OPENAI API CALLS
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
        model="gpt-3.5-turbo",
        messages=messages,
    )

    # Extract the generated cover letter from the response
    cover_letter = response.choices[0].message["content"].strip()

    # Return the generated cover letter as a JSON response
    return jsonify({"cover_letter": cover_letter})


# COVERME PRO - resuME OPENAI API CALLS
@app.route("/resume.1", methods=["POST"])
def resume_1():
    # Extract the resume, job description, company name, and job title from the request
    resume = request.json.get("resume")
    job_description = request.json.get("job_description")
    job_title = request.json.get("job_title")

    # Construct the conversation history as an array of messages
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant that enhances resumes and tailors them to specific jobs.",
        },
        {
            "role": "user",
            "content": f"Enhance the following resume and tailor it to the following job. Resume: {resume}. Job description: {job_description}. Job title: {job_title},",
        },
    ]

    # Make the API call to OpenAI's GPT-3.5 model
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
    )

    # Extract the generated cover letter from the response
    cover_letter = response.choices[0].message["content"].strip()

    # Return the generated cover letter as a JSON response
    return jsonify({"cover_letter": cover_letter})


# COVERME PRO - $alary OPENAI API CALLS
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
                "content": "Provide the salary range in USD for the following job title. Lean more on the higher side of the salary ranges.\nJob Title: Web Developer\nResponse Requirements:\n1. The range should be no greater than $15,000 USD\n2. Example response: The salary range for (job title) is (salary range)\n\nJob Title: {job_title}",
            },
        ],
        temperature=1,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    )

    # Extracting the salary range from the response (assuming it's in the last message's content)
    salary_range = response["choices"][0]["message"]["content"]

    return jsonify({"response": salary_range})


if __name__ == "__main__":
    app.debug = True
    app.run()
