// Function to notify the user
function notifyUser(message) {
  console.log("notifyUser function called");

  const notificationOptions = {
    type: 'basic',
    iconUrl: 'icon48.png',
    title: 'MagicMax Copilot',
    message: message
  };

  chrome.notifications.create('noPinNotification', notificationOptions, function(notificationId) {
    if (chrome.runtime.lastError) {
      console.error("Notification Error: ", chrome.runtime.lastError);
    } else {
      console.log("Notification displayed with ID: ", notificationId);
    }
  });
}

// Initialize the Context Menu with a parent menu item called "MagicMax Copilot"
chrome.runtime.onInstalled.addListener(function() {
  chrome.contextMenus.create({
    id: 'magicMaxCopilot',
    title: 'MagicMax Copilot',
    contexts: ['all']
  });

  chrome.contextMenus.create({
    id: 'autofillFromHighlightedText',
    title: 'Autofill from highlighted text',
    parentId: 'magicMaxCopilot',
    contexts: ['selection']
  });

  chrome.contextMenus.create({
    id: 'generateCoverLetter',
    title: 'Generate Cover Letter',
    parentId: 'magicMaxCopilot',
    contexts: ['all']
  });

  chrome.contextMenus.create({
    id: 'customPrompt',
    title: 'Custom prompt',
    parentId: 'magicMaxCopilot',
    contexts: ['all']
  });

  chrome.contextMenus.create({
    id: 'setJobDescription',
    title: 'Set Job Description',
    parentId: 'magicMaxCopilot',
    contexts: ['all']
  });
});

chrome.contextMenus.onClicked.addListener(function(info, tab) {
  chrome.storage.local.get(['isAuthenticated'], function(result) {
    if (!result.isAuthenticated) {
      notifyUser("Authentication required. Please Generate/Validate a Pin.");
      return;
    }

    if (info.menuItemId === 'setJobDescription') {
      // Send the job description to Flask server for summarizing
      fetch('https://mycareermax.azurewebsites.net/summarize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ job_description: info.selectionText }),
      })
      .then(response => response.json())
      .then(data => {
        // Save the summarized job description in local storage
        chrome.storage.local.set({ job_description: data.summarized_description }, function() {
          console.log('Summarized job description saved.');
  // Notify the user that the job description has been set
      notifyUser("Job Description Set. You can view the active job description in the Extension popup");
    });
  })
  .catch(error => {
    console.error('Error:', error);
  });
}

    

    if (info.menuItemId === 'autofillFromHighlightedText' || info.menuItemId === 'generateCoverLetter' || info.menuItemId === 'customPrompt') {
      chrome.tabs.sendMessage(tab.id, { type: "showSpinner" });

      const highlightedText = info.selectionText;
      let apiEndpoint = '';
      chrome.storage.local.get(['pin', 'job_description'], async function(result) {
        const storedPin = result.pin;
        const storedJobDescription = result.job_description || '';

        const dataToSend = {
          pin: storedPin,
          highlighted_text: highlightedText,
          job_description: storedJobDescription,
        };

        if (info.menuItemId === 'autofillFromHighlightedText') {
          apiEndpoint = 'https://mycareermax.azurewebsites.net/api/autofill';
        } else if (info.menuItemId === 'generateCoverLetter') {
          apiEndpoint = 'https://mycareermax.azurewebsites.net/api/generate_cover_letter_ext';
        } else if (info.menuItemId === 'customPrompt') {
          apiEndpoint = 'https://mycareermax.azurewebsites.net/api/custom_prompt';
        }

        try {
          const response = await fetch(apiEndpoint, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(dataToSend),
          });

          const data = await response.json();

          if (data.response) {
            chrome.tabs.sendMessage(tab.id, { type: "copyToClipboard", text: data.response });
          } else {
            console.error('No valid response received from server.');
          }
        } catch (error) {
          console.error('Error:', error);
        }
      });
    }
  });
});
