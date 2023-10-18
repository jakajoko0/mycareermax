console.log("Content script is running on this page.");

let spinnerStyle = document.createElement('style');
spinnerStyle.type = 'text/css';
spinnerStyle.innerHTML = '@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }';
document.getElementsByTagName('head')[0].appendChild(spinnerStyle);

function showSpinner() {
  let overlay = document.createElement('div');
  overlay.id = 'spinnerOverlay';
  overlay.style.position = 'fixed';
  overlay.style.left = '0';
  overlay.style.top = '0';
  overlay.style.width = '100%';
  overlay.style.height = '100%';
  overlay.style.backgroundColor = 'rgba(0, 0, 0, 0.6)';
  overlay.style.zIndex = '10000';
  overlay.style.display = 'flex';
  overlay.style.justifyContent = 'center';
  overlay.style.alignItems = 'center';

  let spinner = document.createElement('div');
  spinner.id = 'loadingSpinner';
  spinner.style.border = '5px solid transparent';
  spinner.style.borderTopColor = 'blue';
  spinner.style.borderRadius = '50%';
  spinner.style.width = '50px';
  spinner.style.height = '50px';
  spinner.style.animation = 'spin 1s linear infinite';

  overlay.appendChild(spinner);
  document.body.appendChild(overlay);
}

function removeSpinner() {
  let overlay = document.getElementById('spinnerOverlay');
  if (overlay) {
    document.body.removeChild(overlay);
  }
}

let clipboardTooltip = document.createElement('span');
clipboardTooltip.innerHTML = "Ready To Paste";
clipboardTooltip.style.position = "absolute";
clipboardTooltip.style.fontSize = "16px";
clipboardTooltip.style.zIndex = "9999";
clipboardTooltip.style.backgroundColor = "white";
clipboardTooltip.style.border = "1px solid black";
clipboardTooltip.style.padding = "5px";
clipboardTooltip.style.display = "none";
document.body.appendChild(clipboardTooltip);

function copyTextToClipboard(text) {
  let currentScrollPos = window.pageYOffset;

  var textArea = document.createElement("textarea");
  textArea.value = text;
  textArea.style.position = 'fixed';
  document.body.appendChild(textArea);
  textArea.focus();
  textArea.select();
  document.execCommand('copy');
  document.body.removeChild(textArea);
  window.scrollTo(0, currentScrollPos);
  removeSpinner();
}

function showTooltip(event) {
  clipboardTooltip.style.left = event.clientX + window.scrollX + 'px';
  clipboardTooltip.style.top = event.clientY + window.scrollY + 'px';
  clipboardTooltip.style.display = 'inline';
  setTimeout(() => {
    clipboardTooltip.style.display = 'none';
  }, 3000);
}

chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
  if (request.type === 'showSpinner') {
    showSpinner();
  } else if (request.type === 'copyToClipboard') {
    copyTextToClipboard(request.text);
    document.addEventListener('mousemove', function onMouseMove(event) {
      showTooltip(event);
      document.removeEventListener('mousemove', onMouseMove);
    });
  }
});
