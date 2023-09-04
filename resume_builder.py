from flask import Flask, render_template, request, jsonify
import os
import openai
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()


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
            [Full Name (in capital letters)]\\n[email]\\n[phone number]\\n[city, state]\\n[linkedin profile]\\n[website]\\n\\nSUMMARY\\n\\n[Use this model: (Soft skill) (Most Recent Job Title) who is passionate about (your stance on the industry).\\n\\nWORK EXPERIENCE\\n\\n[Job Title] | [Company] | [Location]\\n[Date (MMYYY)]\\n[Responsibilities listed with bullet point (•) and using this model: (Action verb) + (Cause) + (Effect) + (Measurable Outcome).]\\n\\nEDUCATION\\n\\n[School Name], [City]\\n[Degree] in [Major] | [Dates Attended (MM/YYYY)]\\n\\nSKILLS\\n\\n[Use bullet points (•) for each skill]

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

    return render_template("resume-builder.html")
