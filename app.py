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
openai.api_key = os.getenv('OPENAI_API_KEY')


JOBS_API_URL = "https://jsearch.p.rapidapi.com/search"


def fetch_jobs_from_rapidapi(query):
    url = "https://jsearch.p.rapidapi.com/search"
    headers = {
        "X-RapidAPI-Key": "04c645fbbdmshf581fe252de3b82p178cedjsn43d2da570f56",
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }
    params = {"query": query, "page": "1", "num_pages": "1"}

    response = requests.get(url, headers=headers, params=params)
    print(f"API Response: {response.json()}")
    if response.status_code == 200:
        return response.json()
    else:
        return {}


# Create a Flask app instance and configure it
app = Flask(__name__)
app.config['DEBUG'] = True
app.config['PROPAGATE_EXCEPTIONS'] = True

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# API keys
RAPIDAPI_KEY = "04c645fbbdmshf581fe252de3b82p178cedjsn43d2da570f56"
RAPIDAPI_HOST = "jsearch.p.rapidapi.com"
RAPIDAPI_URL = "https://jsearch.p.rapidapi.com/search"

openai.api_key = os.getenv('OPENAI_API_KEY')


# Route to handle the "/resume-analysis" endpoint
@app.route('/resume-analysis')
def resume_analysis():
    return render_template('resume_analysis.html')

# Route to handle the root URL (homepage)
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/cover-letter-generator')
def cover_letter_generator():
    return render_template('cover_letter_generator.html')

@app.route('/resume-enhancer')
def resume_enhancer():
    return render_template('resume_enhancer.html')

@app.route('/jobs-api')
def jobs_api():
    return render_template('jobs_api.html')

@app.route('/interview-prep')
def interview_prep():
    return render_template('interview_prep.html')

@app.route('/application-questions')
def application_questions():
    return render_template('application_questions.html')

@app.route('/analyze-resume', methods=['POST'])
def analyze_resume():
    # Extract the content from the request
    resume_content = request.form.get('resume')
    
    # Construct the messages for the OpenAI API
    messages = [
        {"role": "system", "content": "You are a helpful assistant that reviews and provides feedback on resumes."},
        {"role": "user", "content": f"Review and rate the following resume on a scale from 1 (lowest) to 5 (highest). Give your reasoning in a detailed analysis with tips and suggestions for improvement. Make it no more than 250 words: {resume_content}"}
    ]
    
    # Send the messages to the OpenAI API
    response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
    
    # Extract the model's reply from the response
    feedback = response['choices'][0]['message']['content'].strip()
    
    # Return the feedback to the front end
    return jsonify({'feedback': feedback})





# Route to handle the file upload
@app.route('/upload-docx', methods=['POST'])
def upload_docx():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if file and file.filename.endswith('.docx'):
        # Process the uploaded DOCX file and extract the text content
        try:
            document = Document(file)
            # Extract text content from the document
            docx_content = '\n'.join(paragraph.text for paragraph in document.paragraphs)
            
            # Return the content in the JSON response
            return jsonify({'content': docx_content}), 200
        except Exception as e:
            return jsonify({'error': f'Error processing the file: {e}'}), 500
    else:
        return jsonify({'error': 'Invalid file format. Only .docx files are allowed.'}), 400

# Route to handle the Coverme button to generate cover
@app.route('/generate-cover-letter', methods=['POST'])
def generate_cover_letter():
    # Extract the content from the request
    resume_content = request.form.get('resume')
    job_description = request.form.get('job_description')
    job_title = request.form.get('job_title')
    company_name = request.form.get('company_name')
    focus_areas = request.form.get('focus_areas')

    # Construct the messages for the OpenAI API
    messages = [
        {"role": "system", "content": "You are a helpful assistant that generates personalized cover letters."},
        {"role": "user", "content": f"Generate a cover letter for the following job. Resume: {resume_content}. Job description: {job_description}. Job title: {job_title}. Company name: {company_name}. Focus areas: {focus_areas}"}
    ]
    
    # Send the messages to the OpenAI API
    response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
    
    # Extract the model's reply from the response
    cover_letter = response['choices'][0]['message']['content'].strip()
    
    # Return the cover letter to the front end
    return jsonify({'cover_letter': cover_letter})



@app.route('/jobs_api.html')
def index():
    return open("jobs_api.html").read()

@app.route('/search-rapidapi-jobs', methods=['POST'])
def search_rapidapi_jobs():
    location = request.form.get('location')
    keywords = request.form.get('keywords')

    query = f"{keywords} in {location}"
    response = fetch_jobs_from_rapidapi(query)

    print("RapidAPI Response:", response)  # Add this line for debugging

    # Ensure the 'jobs' property always exists in the response
    jobs = response.get('data', [])
    return jsonify({"jobs": jobs})

if __name__ == '__main__':
    app.run()