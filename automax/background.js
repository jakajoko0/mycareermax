// Initialize the context menu
chrome.runtime.onInstalled.addListener(function() {
  chrome.contextMenus.create({
    id: "autofillWithMagicMax",
    title: "AutoFill With MagicMax",
    contexts: ["selection"],
  });
});

// Add a click event listener for the context menu item
chrome.contextMenus.onClicked.addListener(function(info, tab) {
  if (info.menuItemId === "autofillWithMagicMax") {
    const highlightedText = info.selectionText;
    
    // Retrieve the stored PIN
    chrome.storage.local.get(['pin'], async function(result) {
      const storedPin = result.pin;
      if (!storedPin) {
        console.error('No PIN stored.');
        return;
      }

      // Send the highlighted text and PIN to Flask
      const dataToSend = {
        pin: storedPin,
        highlighted_text: highlightedText,
      };

      try {
        const response = await fetch('http://localhost:5000/api/autofill', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(dataToSend),
        });

        const data = await response.json();
        console.log('Server Response:', data);

        if (data.response) {
          console.log('Response from server:', data.response);

          // Send a message to content.js to copy the data to the clipboard
          chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
            chrome.tabs.sendMessage(tabs[0].id, {type: "copyToClipboard", text: data.response});
          });

        } else {
          console.error('No valid response received from server.');
        }
      } catch (error) {
        console.error('Error:', error);
      }
    });
  }
});
