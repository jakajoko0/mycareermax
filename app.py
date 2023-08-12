# Import necessary libraries
import os
import logging
import requests
from docx import Document
from flask import Flask, render_template, request, jsonify
import openai

import requests

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Now you can access the OPENAI_API_KEY environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")
print(os.getenv("OPENAI_API_KEY"))


JOBS_API_URL = "https://jsearch.p.rapidapi.com/search"


def fetch_jobs_from_rapidapi(query):
    url = "https://jsearch.p.rapidapi.com/search"
    headers = {
        "X-RapidAPI-Key": "04c645fbbdmshf581fe252de3b82p178cedjsn43d2da570f56",
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
    }
    params = {"query": query, "num_pages": "1"}

    response = requests.get(url, headers=headers, params=params)
    print(f"API Response: {response.json()}")
    if response.status_code == 200:
        return response.json()
    else:
        return {}


# Create a Flask app instance and configure it
app = Flask(__name__)
app.config["DEBUG"] = True
app.config["PROPAGATE_EXCEPTIONS"] = True

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

# API keys
RAPIDAPI_KEY = "04c645fbbdmshf581fe252de3b82p178cedjsn43d2da570f56"
RAPIDAPI_HOST = "jsearch.p.rapidapi.com"
RAPIDAPI_URL = "https://jsearch.p.rapidapi.com/search"

openai.api_key = os.getenv("OPENAI_API_KEY")


# Route to handle the "/resume-analysis" endpoint
@app.route("/resume-analysis")
def resume_analysis():
    return render_template("resume_analysis.html")


# Route to handle the root URL (homepage)
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


@app.route("/jobs-api")
def jobs_api():
    return render_template("jobs_api.html")


@app.route("/interview-prep")
def interview_prep():
    return render_template("interview_prep.html")


@app.route("/application-questions")
def application_questions():
    return render_template("application_questions.html")


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


# Route to handle the file upload
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


# Route to handle the Coverme button to generate cover
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


# INTERVIEW SIMULATOR
# Question Generator Call to openai
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


# CareerClick RapidAPI Routes
# RapidAPI configuration
RAPIDAPI_KEY = "04c645fbbdmshf581fe252de3b82p178cedjsn43d2da570f56"
RAPIDAPI_HOST = "jsearch.p.rapidapi.com"
RAPIDAPI_BASE_URL = "https://jsearch.p.rapidapi.com"
headers = {"X-RapidAPI-Key": RAPIDAPI_KEY, "X-RapidAPI-Host": RAPIDAPI_HOST}


@app.route("/fetch-job-listings", methods=["POST"])
def fetch_job_listings():
    query = request.json.get("query")
    location = request.json.get("location")
    # Construct the API URL
    url = f"{RAPIDAPI_BASE_URL}/search?query={query} in {location}&num_pages=1"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({"error": "Failed to fetch job listings"}), 500


@app.route("/fetch-job-details", methods=["POST"])
def fetch_job_details():
    query = request.json.get("query")
    # Construct the API URL for detailed information
    url = f"{RAPIDAPI_BASE_URL}/search-filters?query={query}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({"error": "Failed to fetch job details"}), 500


@app.route("/fetch-search-filters", methods=["POST"])
def fetch_search_filters():
    query = request.json.get("query")
    # Construct the API URL for search filters
    url = f"{RAPIDAPI_BASE_URL}/search-filters?query={query}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({"error": "Failed to fetch search filters"}), 500


# CareerClick OpenAI API Route
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
        max_tokens=500,  # Set a limit on the length of the generated cover letter
    )

    # Extract the generated cover letter from the response
    cover_letter = response.choices[0].message["content"].strip()

    # Return the generated cover letter as a JSON response
    return jsonify({"cover_letter": cover_letter})


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
        max_tokens=500,  # Set a limit on the length of the generated cover letter
    )

    # Extract the generated cover letter from the response
    cover_letter = response.choices[0].message["content"].strip()

    # Return the generated cover letter as a JSON response
    return jsonify({"cover_letter": cover_letter})


@app.route("/upload-search", methods=["POST"])
def upload_search():
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

        # Salary button


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
