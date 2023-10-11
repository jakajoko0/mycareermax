console.log("Content script is running on this page.");

// Create clipboard tooltip
let clipboardTooltip = document.createElement('span');
clipboardTooltip.innerHTML = "Ready To Paste";
clipboardTooltip.style.position = "absolute";
clipboardTooltip.style.fontSize = "16px";
clipboardTooltip.style.zIndex = "9999";
clipboardTooltip.style.backgroundColor = "white";
clipboardTooltip.style.border = "1px solid black";
clipboardTooltip.style.padding = "5px";
clipboardTooltip.style.display = "none";  // Initially set to 'none'
document.body.appendChild(clipboardTooltip);

// Function to copy text to clipboard
function copyTextToClipboard(text) {
  console.log("Active element before copy:", document.activeElement);  // Debug line
  
  var textArea = document.createElement("textarea");
  textArea.value = text;
  
  // Append the textarea element to the DOM
  document.body.appendChild(textArea);
  
  // Explicitly set focus to the textarea
  textArea.focus();
  
  // Select the text in the textarea
  textArea.select();
  
  // Execute the "copy" command to copy the selected text to clipboard
  const successful = document.execCommand('copy');
  
  // Log whether the copy command was successful
  console.log('Copy command was ' + (successful ? 'successful' : 'unsuccessful'));
  
  // Remove the textarea element from the DOM
  document.body.removeChild(textArea);
}

// Function to show tooltip
function showTooltip(event) {
  // Position the tooltip at the mouse cursor's position
  clipboardTooltip.style.left = event.clientX + window.scrollX + 'px';
  clipboardTooltip.style.top = event.clientY + window.scrollY + 'px';
  
  // Make the tooltip visible
  clipboardTooltip.style.display = 'inline';
  
  // Remove tooltip after 3 seconds
  setTimeout(() => {
    clipboardTooltip.style.display = 'none';
  }, 3000);
}

// Listen for messages from background.js
chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
  if (request.type === 'sendToChatGPT') {
    // ... Existing logic ...
  } else if (request.type === 'copyToClipboard') {
    console.log('Received message to copy to clipboard:', request.text);
    
    // Call the function to copy text to clipboard
    copyTextToClipboard(request.text);

    // Use a mouse event listener to capture the cursor's position
    document.addEventListener('mousemove', function onMouseMove(event) {
      // Show tooltip
      showTooltip(event);

      // Remove the event listener
      document.removeEventListener('mousemove', onMouseMove);
    });
  }
});
