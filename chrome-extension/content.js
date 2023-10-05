console.log("Content script running");

async function callOpenAI(context, target, shouldConfirm) {
  const resume = localStorage.getItem("resumeFile"); // Always get the latest resume data
  console.log("Resume from localStorage:", resume);  // Debugging line
  
  const apiUrl = "http://localhost:5000/autofill";
  const savedQuestionnaireData = JSON.parse(localStorage.getItem("questionnaireData") || '{}');

  const payload = {
    field_context: context,
    resume_content: resume,
    questionnaire_data: savedQuestionnaireData
  };

  console.log("Payload being sent:", JSON.stringify(payload));  // Debugging line

  const response = await fetch(apiUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error(`API request failed with status ${response.status}`);
  }

  const data = await response.json();
  const suggestedText = data.response;

  if (shouldConfirm) {
    const userConfirmed = confirm(`Use this suggested text? ${suggestedText}`);
    if (userConfirmed) {
      target.value = suggestedText;
    }
  } else {
    target.value = suggestedText;
  }
}

// Function to auto-fill all fields in the form
async function autoFillAllFields() {
  const inputElements = document.querySelectorAll('input, textarea');
  for (const element of inputElements) {
    const context = element.placeholder || element.getAttribute('aria-label') || element.getAttribute('name') || '';
    if (context) {
      await callOpenAI(context, element, false).catch(console.error);
    }
  }
}

// Listen for focus events on input and textarea elements
document.body.addEventListener('focus', function(event) {
  const target = event.target;
  if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') {
    const context = target.placeholder || target.getAttribute('aria-label') || target.getAttribute('name') || '';
    callOpenAI(context, target, false).catch(console.error);
  }
}, true);

// Listen for messages from the background or popup script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  try {
    if (request.action === "triggerChatGPT") {
      const activeElement = document.activeElement;
      if (activeElement && (activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA')) {
        const context = activeElement.placeholder || activeElement.getAttribute('aria-label') || activeElement.getAttribute('name') || '';
        callOpenAI(context, activeElement, true).catch(console.error);
        sendResponse({ status: "success", message: "Auto-fill completed." });
      }
    } else if (request.action === "initiateAutoFill") {
      autoFillAllFields().catch(console.error);
      sendResponse({ status: "success", message: "Initiated auto-fill." });
    }
  } catch (error) {
    console.error("Error in onMessage event listener:", error);
    sendResponse({ status: "error", message: error.message });
  }
  return true; // This keeps the message channel open for sendResponse
});
