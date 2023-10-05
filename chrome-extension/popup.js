// Event listener for DOMContentLoaded
document.addEventListener("DOMContentLoaded", function () {
  // DOM Elements
  const elements = {
    pinStatus: document.getElementById("pinStatus"),
    pinInput: document.getElementById("pinInput"),
    pinButton: document.getElementById("pinButton"),
    emailInput: document.getElementById("emailInput"),
    resumeUpload: document.getElementById("resumeUpload"),
    genderSelect: document.getElementById("genderSelect"),
    dobInput: document.getElementById("dobInput"),
    citizenshipSelect: document.getElementById("citizenshipSelect"),
    educationSelect: document.getElementById("educationSelect"),
    questionnaireStatus: document.getElementById("questionnaireStatus"),
    resumeStatus: document.getElementById("resumeStatus"),
    coverLetterStatus: document.getElementById("coverLetterStatus"),
    jobDescription: document.getElementById("jobDescription"),
    generatePinButton: document.getElementById("generatePinButton"),
    submitQuestionnaire: document.getElementById("submitQuestionnaire"),
    autoFillButton: document.getElementById("autoFillButton"),
    generateCoverLetterButton: document.getElementById("generateCoverLetterButton")
  };

  // Check if any elements are missing and log them
  for (const [key, value] of Object.entries(elements)) {
    if (!value) {
      console.error(`Element ${key} could not be found in the DOM.`);
      return;
    }
  }

  // Chrome Context Menus
  chrome.contextMenus.removeAll(function () {
    chrome.contextMenus.create({
      "id": "autofillWithChatGPT",
      "title": "Auto-fill with ChatGPT",
      "contexts": ["editable"]
    });
  });

  // Event Listener for Chrome Context Menus
  chrome.contextMenus.onClicked.addListener(function (info, tab) {
    if (info.menuItemId === "autofillWithChatGPT") {
      chrome.tabs.sendMessage(tab.id, { action: "triggerChatGPT" });
    }
  });

  // API base URL
  const API_BASE_URL = "http://localhost:5000";

  // Async function to generate PIN
  async function generatePin(email) {
    try {
      const apiUrl = `${API_BASE_URL}/generate_pin`;
      const payload = { email: email };
      const response = await fetch(apiUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }

      const data = await response.json();
      elements.pinStatus.innerText = "PIN generated and sent to your email.";
    } catch (error) {
      console.error("Error generating PIN:", error);
      elements.pinStatus.innerText = "Error generating PIN. Please try again.";
    }
  }

  // Async function to validate PIN
  async function validatePin(email, pin) {
    try {
      const apiUrl = `${API_BASE_URL}/validate_pin`;
      const payload = { email: email, pin: pin };
      const response = await fetch(apiUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }

      const data = await response.json();
      const status = data.status;

      if (status === "success") {
        elements.pinStatus.innerText = "PIN validated successfully.";
      } else {
        elements.pinStatus.innerText = "PIN validation failed.";
      }
    } catch (error) {
      console.error("Error validating PIN:", error);
      elements.pinStatus.innerText = "Error validating PIN. Please try again.";
    }
  }

  // Event Listener for Generate PIN Button
  elements.generatePinButton.addEventListener("click", function () {
    const email = elements.emailInput.value;
    if (email) {
      generatePin(email);
    } else {
      elements.pinStatus.innerText = "Please enter an email.";
    }
  });

  // Event Listener for PIN Button
  elements.pinButton.addEventListener("click", async function () {
    const enteredPin = elements.pinInput.value;
    const email = elements.emailInput.value;
    if (enteredPin && email) {
      await validatePin(email, enteredPin);
    } else {
      elements.pinStatus.innerText = "Please enter a PIN and email.";
    }
  });

  // Event Listener for Resume Upload
  elements.resumeUpload.addEventListener("change", function () {
    const file = this.files[0];
    if (file) {
      const reader = new FileReader();
      reader.addEventListener("load", function () {
        console.log("Resume read:", this.result.substring(0, 100) + "...");  // Log first 100 characters of the resume
        localStorage.setItem("resumeFile", this.result);
        elements.resumeStatus.innerText = "Resume has been uploaded.";
      });
      reader.readAsDataURL(file);
    }
  });

  // Function to Save Questionnaire Data
  function saveQuestionnaireData() {
    const questionnaireData = {
      gender: elements.genderSelect.value,
      dob: elements.dobInput.value,
      citizenshipStatus: elements.citizenshipSelect.value,
      educationLevel: elements.educationSelect.value
    };
    localStorage.setItem("questionnaireData", JSON.stringify(questionnaireData));
    elements.questionnaireStatus.textContent = "Questionnaire Status: Completed";
  }

  // Event Listener for Submit Questionnaire Button
  elements.submitQuestionnaire.addEventListener("click", function () {
    saveQuestionnaireData();
  });

  // Event Listeners for Questionnaire Fields
  elements.genderSelect.addEventListener("change", saveQuestionnaireData);
  elements.dobInput.addEventListener("change", saveQuestionnaireData);
  elements.citizenshipSelect.addEventListener("change", saveQuestionnaireData);
  elements.educationSelect.addEventListener("change", saveQuestionnaireData);

  // Load Saved Questionnaire Data
  const savedQuestionnaireData = JSON.parse(localStorage.getItem("questionnaireData"));
  if (savedQuestionnaireData) {
    elements.genderSelect.value = savedQuestionnaireData.gender || "";
    elements.dobInput.value = savedQuestionnaireData.dob || "";
    elements.citizenshipSelect.value = savedQuestionnaireData.citizenshipStatus || "";
    elements.educationSelect.value = savedQuestionnaireData.educationLevel || "";
    elements.questionnaireStatus.textContent = "Questionnaire Status: Completed";
  } else {
    elements.questionnaireStatus.textContent = "Questionnaire Status: Not Completed";
  }

  // Event Listener for AutoFill Button
  elements.autoFillButton.addEventListener("click", function () {
    chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
      const activeTab = tabs[0];
      if (activeTab && activeTab.id) {
        chrome.tabs.sendMessage(activeTab.id, { action: "initiateAutoFill" }, function (response) {
          if (chrome.runtime.lastError) {
            console.error(chrome.runtime.lastError.message);
          }
        });
      }
    });
  });

  // Async function to generate cover letter based on job description
  async function generateCoverLetter(jobDescription) {
    try {
      // Placeholder for API call to generate cover letter using jobDescription
      // const response = await fetch(`${API_BASE_URL}/generate_cover_letter`, { method: "POST", body: JSON.stringify({ prompt: jobDescription }) });
      // const data = await response.json();
      // const coverLetter = data.coverLetter;

      const coverLetter = `Sample Cover Letter based on job description: ${jobDescription}`; // Placeholder
      elements.coverLetterStatus.innerText = coverLetter;
    } catch (error) {
      console.error("Error generating cover letter:", error);
      elements.coverLetterStatus.innerText = "Error generating cover letter. Please try again.";
    }
  }

  // Event Listener for Generate Cover Letter Button
  elements.generateCoverLetterButton.addEventListener("click", function () {
    const jobDescription = elements.jobDescription.value;
    if (jobDescription) {
      generateCoverLetter(jobDescription);
    } else {
      elements.coverLetterStatus.innerText = "Please enter a job description.";
    }
  });
});
