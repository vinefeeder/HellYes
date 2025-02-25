// contentScript.js
console.log("Content script loaded");

// Function to extract title and episode information
function extractTitle() {
    // Find the title inside .tit-holder > h3
    const titleElement = document.querySelector('.tit-holder h3');
    const titleText = titleElement ? titleElement.textContent.trim() : "";

    // Find the episode info, if available (e.g. a span with classes 'episode episode-seen')
    const episodeElement = document.querySelector('span.episode.episode-seen');
    const episodeText = episodeElement ? episodeElement.textContent.trim() : "";

    // Combine the episode with the title if the episode exists
    if (episodeText) {
        return `${titleText} - ${episodeText}`;
    }
    return titleText;
}

// Function to check and send the title if found
function checkAndSendTitle() {
    const pageTitle = extractTitle();
    if (pageTitle) {
        console.log("Title found:", pageTitle);
        chrome.runtime.sendMessage({ action: "updateTitle", title: pageTitle });
        // Once the title is found, disconnect the observer if it's no longer needed
        observer.disconnect();
    }
}

// Create a MutationObserver to monitor changes in the document body
const observer = new MutationObserver((mutationsList, obs) => {
    // You can check for specific mutations if needed
    checkAndSendTitle();
});

// Start observing the document body for added nodes, attribute changes, etc.
observer.observe(document.body, {
    childList: true,
    subtree: true
});

// Also check once on initial load, in case the element is already present
checkAndSendTitle();
