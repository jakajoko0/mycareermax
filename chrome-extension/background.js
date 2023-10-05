// Remove existing context menu to avoid duplicates
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.removeAll(function() {
    chrome.contextMenus.create({
      id: "autofillWithChatGPT",
      title: "Auto-fill with ChatGPT",
      contexts: ["editable"],
    });
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "autofillWithChatGPT") {
    chrome.tabs.sendMessage(tab.id, { action: "triggerChatGPT" });
  }
});
