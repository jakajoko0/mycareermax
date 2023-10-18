document.addEventListener("DOMContentLoaded", function () {
    console.log("DOM loaded");

    // Initialize variables
    let storedPin = null;

    // Fetch initial message from the Flask API
    fetch('https://mycareermax.azurewebsites.net/api/message')
        .then(response => response.json())
        .then(data => {
            document.getElementById("message").textContent = data.message;
        })
        .catch(error => {
            document.getElementById("message").textContent = "Failed to fetch data: " + error;
        });

    // Check local storage for authentication status and job description
    chrome.storage.local.get(['pin', 'isAuthenticated', 'job_description'], function (result) {
        const elementsToHide = [
            'goToDashboard',
            'savedJobsContainer',
            'jobDescription',
            'resumeFilename',
            'savedJobsHeader',
            'activeJobDescriptionHeader'
        ];

        if (result.isAuthenticated) {
            // Show the relevant elements
            elementsToHide.forEach(id => {
                document.getElementById(id).style.display = 'block';
            });

            // Hide authentication-related fields
            document.getElementById("email").style.display = "none";
            document.getElementById("emailLabel").style.display = "none";
            document.getElementById("generatePin").style.display = "none";
        } else {
            // Hide the relevant elements
            elementsToHide.forEach(id => {
                document.getElementById(id).style.display = 'none';
            });

            if (result.pin) {
                storedPin = result.pin;
                document.getElementById("generatePin").style.display = "none";
                document.getElementById("pinInput").style.display = "block";
                document.getElementById("validatePin").style.display = "block";
            }
        }

        if (result.job_description) {
            document.getElementById("jobDescription").value = result.job_description;
        }

        // Fetch saved jobs and resume filename if a PIN is stored
        if (result.pin) {
            fetchSavedJobs(result.pin);
            fetchResumeFilename(result.pin);
        }
    });

    // Initialize a variable to keep track of the current job index
    let currentJobIndex = 0;
    let allJobs = [];

    // Function to display saved jobs
// Function to display saved jobs
function displaySavedJobs() {
    const savedJobsContainer = document.getElementById("savedJobsContainer");
    savedJobsContainer.innerHTML = ""; // Clear previous entries

    allJobs.forEach((job, index) => {
        const jobDiv = document.createElement("div");
        jobDiv.className = "savedJobBox"; // Style the div

        const jobTitle = document.createElement("h3");
        jobTitle.textContent = job.job_title;

        const jobCompany = document.createElement("p");
        jobCompany.textContent = job.company_name;  // Make sure the attribute name matches your Flask route's output

        const jobLink = document.createElement("a");
        jobLink.href = job.job_link;  // Make sure the attribute name matches your Flask route's output
        jobLink.target = "_blank";
        jobLink.textContent = "View Job";

        jobDiv.appendChild(jobTitle);
        jobDiv.appendChild(jobCompany);
        jobDiv.appendChild(jobLink);

        savedJobsContainer.appendChild(jobDiv);
    });
}

    // Function to fetch saved jobs
    function fetchSavedJobs(pin) {
        fetch('https://mycareermax.azurewebsites.net/api/get_saved_jobs_ext', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ pin: pin })
        })
        .then(response => response.json())
        .then(data => {
            if (data.saved_jobs) {
                allJobs = data.saved_jobs;
                displaySavedJobs(); // Display the saved jobs
            }
        })
        .catch(error => {
            console.error("Failed to fetch saved jobs:", error);
        });
    }

    // Function to fetch resume filename
    function fetchResumeFilename(pin) {
        fetch('https://mycareermax.azurewebsites.net/api/get_resume_filename', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ pin: pin })
        })
        .then(response => response.json())
        .then(data => {
            if (data.filename) {
                const resumeFilenameDiv = document.getElementById("resumeFilename");
                resumeFilenameDiv.innerHTML = `<span style="color: white;">Active Resume: ${data.filename}</span>`;
            }
        })
        .catch(error => {
            console.error("Failed to fetch resume filename:", error);
        });
    }

    // Event Listener for Generate Pin button
    document.getElementById("generatePin").addEventListener("click", function () {
        const email = document.getElementById("email").value;

        fetch('https://mycareermax.azurewebsites.net/api/generate_pin', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email: email })
        })
        .then(response => response.json())
        .then(data => {
            if (data.pin) {
                chrome.storage.local.set({ 'pin': data.pin }, function () {
                    alert("Email sent containing Pin");
                    document.getElementById("generatePin").style.display = "none";
                    document.getElementById("pinInput").style.display = "block";
                    document.getElementById("validatePin").style.display = "block";
                });
            }
        })
        .catch(error => {
            alert("Failed to generate PIN: " + error);
        });
    });

    // Event Listener for Validate Pin button
    document.getElementById("validatePin").addEventListener("click", function () {
        const enteredPin = document.getElementById("pinInput").value;
        const email = document.getElementById("email").value;

        fetch('https://mycareermax.azurewebsites.net/api/validate_pin', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email: email, pin: enteredPin })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                chrome.storage.local.set({ 'isAuthenticated': true }, function () {
                    document.getElementById("email").style.display = "none";
                    document.getElementById("emailLabel").style.display = "none";
                    document.getElementById("generatePin").style.display = "none";
                    document.getElementById("pinInput").style.display = "none";
                    document.getElementById("validatePin").style.display = "none";
                    const elementsToShow = [
                        'goToDashboard',
                        'savedJobsContainer',
                        'jobDescription',
                        'resumeFilename',
                        'savedJobsHeader',
                        'activeJobDescriptionHeader'
                    ];
                    elementsToShow.forEach(id => {
                        document.getElementById(id).style.display = 'block';
                    });
                });
            } else {
                alert("PIN validation failed: " + data.message);
            }
        })
        .catch(error => {
            alert("Failed to validate PIN: " + error);
        });
    });



    // Add click event for the 'goToDashboard' button
    document.getElementById("goToDashboard").addEventListener("click", function () {
        window.open('https://app.mycareermax.com/dashboard', '_blank');
    });
});
