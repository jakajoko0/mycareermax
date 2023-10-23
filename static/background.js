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
    contexts: ['all']
  });

  chrome.contextMenus.create({
    id: 'addToTracker',
    title: 'Add to Tracker',
    parentId: 'setJobDescription',
    contexts: ['all']
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
                  application_url: url
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
      console.log("setJobDescription selected, sending job description to summarize");
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
          notifyUser("Job Description Set. You can view the active job description in the Extension popup");
        });
      })
      .catch(error => {
        console.error('Error:', error);
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
// Listen for manual triggers from the test page
chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
  if (request.type === "manualTrigger") {
    const info = { menuItemId: request.action, selectionText: request.selectionText };
    const tab = {}; // Empty tab object as it's not really needed here
    console.log("Manually triggering action:", request.action);
    chrome.contextMenus.onClicked.dispatch(info, tab);
  }
});

