document.addEventListener("DOMContentLoaded", () => {
    const titleInput = document.getElementById("title");
    const manifestCheckbox = document.getElementById("manifestCheckbox");
    const curlCheckbox = document.getElementById("curlCommand");
    const sendButton = document.getElementById("sendButton");

    // Function to check if the button should be enabled
    function updateButtonState() {
        sendButton.disabled = false;
    }

    // Function to update checkbox appearance (green for checked, red for unchecked)
    function updateCheckboxStyle(checkbox, isChecked) {
        checkbox.checked = isChecked;
        checkbox.style.cursor = "default";
        checkbox.style.borderColor = isChecked ? "green" : "red";
    }

    // Get the manifest URL status and title when the popup opens
    chrome.runtime.sendMessage({ action: "getTabData" }, (response) => {
        if (response) {
            // Set title if available
            if (response.title) {
                titleInput.value = response.title;
            }

            // Check if manifest URL is present
            updateCheckboxStyle(manifestCheckbox, !!response.manifestUrl);

            // Check if cURL command is present
            updateCheckboxStyle(curlCheckbox, !!response.curlCommand);

            // Update button state initially
            updateButtonState();
        }
    });

    // Enable button only when all conditions are met
    titleInput.addEventListener("input", updateButtonState);
    manifestCheckbox.addEventListener("change", updateButtonState);
    curlCheckbox.addEventListener("change", updateButtonState);

    // Send data when button is clicked
    sendButton.addEventListener("click", () => {
        const titleValue = titleInput.value;
        chrome.runtime.sendMessage({ action: "sendData", title: titleValue }, (response) => {
            const resultDiv = document.getElementById("result");
            if (response && response.status === "success") {
                resultDiv.textContent = "Data sent successfully! "+response.message;
            } else {
                resultDiv.textContent = "Error: " + (response.error || "Unknown error");
            }
        });
    });
});
