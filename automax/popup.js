document.addEventListener("DOMContentLoaded", function () { 
    // Fetch message from Flask API
    fetch('https://mycareermax.azurewebsites.net/api/message')
        .then(response => response.json())
        .then(data => {
            document.getElementById("message").textContent = data.message;
        })
        .catch(error => {
            document.getElementById("message").textContent = "Failed to fetch data: " + error;
        });

    // Check local storage to decide which UI to show
    chrome.storage.local.get(['pin', 'isAuthenticated'], function (result) {
        if (result.isAuthenticated) {
            // User is authenticated
            const successMessage = document.createElement("div");
            successMessage.textContent = "User authenticated";
            successMessage.style.color = "green";
            document.body.appendChild(successMessage);
        } else if (result.pin) {
            // PIN exists but is not validated yet
            document.getElementById("generatePin").style.display = "none";
            document.getElementById("pinInput").style.display = "block";
            document.getElementById("validatePin").style.display = "block";
        }
    });

    // Generate PIN button functionality
    document.getElementById("generatePin").addEventListener("click", function () {
        const email = document.getElementById("email").value;
        fetch('https://mycareermax.azurewebsites.net/api/generate_pin', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email: email })
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.pin) {
                    chrome.storage.local.set({ 'pin': data.pin }, function () {
                        alert("PIN generated and stored.");
                        // Hide Generate Pin button and show Validate Pin field and button
                        document.getElementById("generatePin").style.display = "none";
                        document.getElementById("pinInput").style.display = "block";
                        document.getElementById("validatePin").style.display = "block";
                    });
                } else {
                    alert("Failed to retrieve PIN from the response.");
                }
            })
            .catch(error => {
                alert("Failed to generate PIN: " + error);
            });
    });

    // Validate PIN button functionality
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
                    // Set isAuthenticated flag in local storage
                    chrome.storage.local.set({ 'isAuthenticated': true }, function () {
                        console.log("User is authenticated.");
                    });

                    // Hide all PIN-related elements
                    document.getElementById("email").style.display = "none";
                    document.getElementById("generatePin").style.display = "none";
                    document.getElementById("pinInput").style.display = "none";
                    document.getElementById("validatePin").style.display = "none";

                    // Show a success message
                    const successMessage = document.createElement("div");
                    successMessage.textContent = "User authenticated";
                    successMessage.style.color = "green";
                    document.body.appendChild(successMessage);
                } else {
                    alert("PIN validation failed: " + data.message);
                }
            })
            .catch(error => {
                alert("Failed to validate PIN: " + error);
            });
    });
 });