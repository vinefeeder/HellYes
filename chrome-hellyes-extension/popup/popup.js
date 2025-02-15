// Get the title when the popup opens
document.addEventListener("DOMContentLoaded", () => {
    chrome.runtime.sendMessage({ action: "getTitle" }, (response) => {
        if (response && response.title && response.title !== "") {
            document.getElementById("title").value = response.title;
        }
    });
});

document.getElementById("sendButton").addEventListener("click", () => {
    const titleValue = document.getElementById("title").value;
    chrome.runtime.sendMessage({ action: "sendData", title: titleValue }, (response) => {
        const resultDiv = document.getElementById("result");
        if (response && response.status === "success") {
            resultDiv.textContent = "Data sent successfully!";
        } else {
            resultDiv.textContent = "Error: " + (response.error || "Unknown error");
        }
    });
});
