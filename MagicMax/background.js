// Function to notify the user
function notifyUser(message) {
  console.log("notifyUser function called with message:", message);
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
  console.log("Creating context menus");
  chrome.contextMenus.create({
    id: 'magicMaxCopilot',
    title: 'MagicMax Copilot',
    contexts: ['all']
  });

  chrome.contextMenus.create({
    id: 'setJobDescription',
    title: 'Set Job Description',
    parentId: 'magicMaxCopilot',
    contexts: ['selection']
  });

  chrome.contextMenus.create({
    id: 'addToTracker',
    title: 'Add to Tracker',
    parentId: 'setJobDescription',
    contexts: ['selection']
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
    id: 'dontTrack',
    title: "Don't Track",
    parentId: 'setJobDescription',
    contexts: ['selection']
  });

  console.log("Context menus created");
});

// Single event listener for context menu clicks
chrome.contextMenus.onClicked.addListener(function(info, tab) {
  console.log("Context menu clicked:", info.menuItemId);
  chrome.storage.local.get(['isAuthenticated'], function(result) {
    if (!result.isAuthenticated) {
      notifyUser("Authentication required. Please Generate/Validate a Pin.");
      return;
    }

    if (info.menuItemId === 'addToTracker') {
      console.log("addToTracker selected, sending job description to summarize");

      // Fetch current tab URL
      chrome.tabs.query({ active: true, lastFocusedWindow: true }, function(tabs) {
        let url = tabs[0].url;
        console.log("Current tab URL:", url);

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
          console.log("Received summarized job description:", data.summarized_description);
          // Save the summarized job description in local storage
          chrome.storage.local.set({ job_description: data.summarized_description }, function() {
            console.log('Summarized job description saved in local storage.');

            // Send summarized job description, pin, and URL to /api/add_job
            chrome.storage.local.get(['pin'], function(result) {
              const storedPin = result.pin;
              console.log("Stored PIN:", storedPin);

fetch('https://mycareermax.azurewebsites.net/api/add_job', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    pin: storedPin,
    job_summary: data.summarized_description,
    job_url: url  // Changed from application_url to job_url
  }),
})
.then(response => response.json())
.then(data => {
  console.log("Received response from /api/add_job:", data);
  // Handle response from /api/add_job
  notifyUser("Job added to tracker.");
})
.catch(error => {
  console.error('Error:', error);
});
            });
          });
        })
        .catch(error => {
          console.error('Error:', error);
        });
      });
    }

  if (info.menuItemId === 'setJobDescription') {
    // Summarize the selected job description and save it in local storage
    fetch('https://mycareermax.azurewebsites.net/summarize', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ job_description: info.selectionText }),
    })
    .then(response => response.json())
    .then(data => {
      chrome.storage.local.set({ job_description: data.summarized_description }, function() {
        notifyUser("Job description set. You can now use it for other features.");
      });
    })
    .catch(error => {
      console.error('Error:', error);
    });
  }

  if (info.menuItemId === 'dontTrack') {
    // Save the selected text as the job description without tracking it
    chrome.storage.local.set({ job_description: info.selectionText }, function() {
      notifyUser("Job description set without tracking. You can now use it for other features.");
    });
  }


    if (info.menuItemId === 'autofillFromHighlightedText' || info.menuItemId === 'generateCoverLetter' || info.menuItemId === 'customPrompt') {
      console.log("Selected:", info.menuItemId, "Sending highlighted text for processing");
      chrome.tabs.sendMessage(tab.id, { type: "showSpinner" });

      const highlightedText = info.selectionText;
      let apiEndpoint = '';
      chrome.storage.local.get(['pin', 'job_description'], async function(result) {
        const storedPin = result.pin;
        const storedJobDescription = result.job_description || '';
        console.log("Stored PIN:", storedPin, "Stored Job Description:", storedJobDescription);

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
            console.log("Received response for", info.menuItemId, ":", data.response);
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


