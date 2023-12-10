import smtplib  # Add this line
from flask import Flask, jsonify, request
import os
import requests
import logging
import pyodbc
import time  # If you're using time.sleep in your code
from smtplib import SMTP
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
# Add any other imports you need

from dotenv import load_dotenv
load_dotenv()  # Load environment variables from a .env file if present




# Initialize Flask app
app = Flask(__name__)

# Database connection
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


# RapidAPI settings
RAPIDAPI_KEY = "04c645fbbdmshf581fe252de3b82p178cedjsn43d2da570f56"
RAPIDAPI_HOST = "jsearch.p.rapidapi.com"
RAPIDAPI_BASE_URL = "https://jsearch.p.rapidapi.com/search"

def fetch_users_for_alerts():
    connection = create_connection()
    try:
        with connection.cursor() as cursor:
            query = """
                SELECT u.id, u.email
                FROM users u
                INNER JOIN UserDetails ud ON u.id = ud.UserID
                WHERE ud.JobAlertNotifications = 'yes'
            """
            cursor.execute(query)
            return cursor.fetchall()
    except Exception as e:
        logging.error(f"Failed to fetch users: {e}")
        return []
    finally:
        connection.close()


def fetch_user_preferences(user_id):
    """
    Fetches a user's desired job title, location, and work type from the database.

    Args:
        user_id (int): The user's unique identifier.

    Returns:
        dict: A dictionary containing the user's preferences, or None if not found.
    """

    with create_connection() as connection:
        cursor = connection.cursor()

        try:
            cursor.execute("SELECT DesiredJobTitle, DesiredJobLocation, DesiredWorkType FROM UserDetails WHERE UserID=?", (user_id,))
            row = cursor.fetchone()

            if row:
                return {
                    "DesiredJobTitle": row[0],
                    "DesiredJobLocation": row[1],
                    "DesiredWorkType": row[2],
                }

            return None
        except Exception as e:
            logging.error(f"Failed to fetch user preferences: {e}")
            return None


def fetch_job_listings(user_preferences):
    """
    Fetches job listings based on a user's desired job title, location, and work type.

    Args:
        user_preferences (dict): A dictionary containing the user's preferences.

    Returns:
        list: A list of dictionaries containing job data.
    """

    query = user_preferences["DesiredJobTitle"]
    location = user_preferences["DesiredJobLocation"]
    remote = "true" if user_preferences["DesiredWorkType"] == "Remote" else "false"
    page = 1

    url = f"{RAPIDAPI_BASE_URL}?query={query} in {location}&page={page}&remote_jobs_only={remote}"

    try:
        response = requests.get(url, headers={"X-RapidAPI-Key": RAPIDAPI_KEY, "X-RapidAPI-Host": RAPIDAPI_HOST})
        response.raise_for_status()
        jobs_data = response.json()
        return jobs_data["data"]
    except requests.RequestException as e:
        logging.error(f"Request failed: {e}")
        return []


def send_job_alert_email(email, job_listings, sender_alias="mycareermax-jobs@mycareermax.com"):

    """
    Sends an email containing job listings to a user.

    Args:
        email (str): The user's email address.
        job_listings (list): A list of dictionaries containing job data.
    """

    smtp_server = "smtp.office365.com"
    smtp_port = 587
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    sender_email = sender_alias if sender_alias else smtp_username
    recipients = [email]
    subject = "Your myCAREERMAX Matches Are Here!"

    # Add align="center" attribute to the img tag to center the image horizontally
    body = f"""
<img src="https://drive.google.com/uc?export=download&id=1Q-RAGQesLg0dXQk-Hbgvh2RoWYqp7032" alt="Job Listing Header" style="max-width: 100%; height: auto; margin-bottom: 20px;" align="center">

<ul>
{format_job_listings(job_listings)}
</ul>

    <p style="margin-top: 20px;">
        If you need to update your job preferences or would like to be removed from these automated emails, please visit the 
        <a href="https://app.mycareermax.com/myprofile">My Profile &gt; Edit Preferences</a> 
        section on the <a href="https://app.mycareermax.com/login">myCAREERMAX</a>  website or mobile app. This way, we can ensure that we always send you the most relevant job opportunities.
    </p>
    
    <p style="margin-top: 10px; color: purple;">
        Thank you for allowing us to be a part of your career journey. We wish you the best in your job search and are here to support you every step of the way. Your success is our success, and we look forward to celebrating each milestone with you.
    </p>

    <p style="margin-top: 10px; color: purple;">
        Cheers,<br>
        The myCAREERMAX Team
    </p>
    """
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html"))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(sender_email, recipients, msg.as_string())
        server.quit()
        logging.info(f"Job alert email sent successfully to {email}")
    except Exception as e:
        logging.error(f"Failed to send email: {str(e)}")


# Function to format job listings as HTML
def format_job_listings(job_listings):
    formatted_listings = "<ul style='list-style-type:none; padding: 0;'>"
    default_logo = "https://drive.google.com/uc?export=download&id=1Xgk3urVjJ_Yy40FObqE4B6czESeyKoIc"
    for job in job_listings:
        title = job.get('job_title', 'No Title Available')
        company = job.get('employer_name', 'No Company Information')
        employment_type = job.get('job_employment_type', 'Not Specified')
        apply_link = job.get('job_apply_link', '#')
        is_remote = 'Yes' if job.get('job_is_remote', False) else 'No'
        city = job.get('job_city', 'No City Info')
        publisher = job.get('job_publisher', 'Not Available')
        employer_logo = job.get('employer_logo') or default_logo  # Use default logo if not available

        job_info = f"""
        <li style='border: 1px solid #ddd; padding: 10px; margin-bottom: 20px; border-radius: 5px; display: flex; align-items: center;'>
            <img src='{employer_logo}' alt='{company} Logo' style='max-width: 50px; max-height: 50px; margin-right: 10px;' onerror='this.src="{default_logo}";'>
            <div>
                <h3 style='margin-bottom: 0;'>{title}</h3>
                <p style='margin-top: 5px;'><strong>{company}</strong> <br>
                Employment Type: {employment_type}<br>
                Remote: {is_remote}<br>
                City: {city}<br>
                Via: {publisher}</p>
                <a href='{apply_link}' style='text-decoration: none;'>
                    <button style='background-color: #4CAF50; color: white; padding: 8px 10px; border-radius: 5px; text-align: center; display: inline-block; font-size: 14px; margin: 4px 2px; cursor: pointer;'>Apply Here</button>
                </a>
            </div>
        </li>
        """
        formatted_listings += job_info
    formatted_listings += "</ul>"
    return formatted_listings





# Route to fetch job listings for alerts and send job alert email
@app.route("/fetch-and-send-job-alerts", methods=["POST"])
def fetch_and_send_job_alerts():
    user_id = request.json.get('user_id')
    email = request.json.get('email')

    # Fetch user preferences from the database
    user_preferences = fetch_user_preferences(user_id)

    if not user_preferences:
        return jsonify({"error": "User has not opted for alerts or preferences not set"}), 400

    # Fetch job listings based on user preferences
    job_listings = fetch_job_listings(user_preferences)

    if job_listings:
        send_job_alert_email(email, job_listings)
        return jsonify({"message": "Job alert email sent successfully"})
    else:
        return jsonify({"message": "No job listings found"})

@app.route("/trigger-job-alerts", methods=["GET"])
def trigger_job_alerts():
    users = fetch_users_for_alerts()

    for user_id, email in users:
        user_preferences = fetch_user_preferences(user_id)
        if user_preferences:
            job_listings = fetch_job_listings(user_preferences)
            if job_listings:
                send_job_alert_email(email, job_listings)
                logging.info(f"Job alert email sent successfully to {email}")
            else:
                logging.info(f"No job listings found for user {user_id}")
        else:
            logging.info(f"No preferences set for user {user_id}")

    return jsonify({"message": "Processed job alerts for users"})



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)