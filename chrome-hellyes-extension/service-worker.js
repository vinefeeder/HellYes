// Array to store matching URLs
let manifestUrl = "";
let licenseData = "";
let licenseHeaders = [];
let headerString = "";
let licenseUrl = "";
let title = "";

let getProgramInfoHeaders = {};
// Listen for network requests and filter by "manifest" or "license"
chrome.webRequest.onCompleted.addListener(
    (details) => {
        // Only process GET requests
        if (details.method !== "GET") return;

        // Exclude requests that are for images
        if (details.type === "image") return;
        if (/manifest|license/i.test(details.url)) {
            manifestUrl = details.url;
            console.log("Matched URL:", details.url);
        }
    },
    { urls: ["<all_urls>"] }
);

// Helper: convert raw bytes to a cURL-friendly escaped string
function bytesToEscapedString(rawBytes) {
    const uint8 = new Uint8Array(rawBytes);
    // Convert each byte to "\xHH"
    return Array.from(uint8)
        .map(b => "\\x" + b.toString(16).padStart(2, "0"))
        .join("");
}
chrome.webRequest.onBeforeRequest.addListener(
    (details) => {
        if (details.method === "POST" && /license/i.test(details.url)) {

            let dataStr = "";

            if (details.requestBody) {
                if (details.requestBody.raw && details.requestBody.raw.length > 0) {
                    // For binary data, do not assume UTF-8; convert to escaped hex
                    dataStr = bytesToEscapedString(details.requestBody.raw[0].bytes);
                } else if (details.requestBody.formData) {
                    // For form data, you could JSON-stringify it or build key=value pairs
                    dataStr = JSON.stringify(details.requestBody.formData);
                }
            }

            licenseData = dataStr
            licenseUrl = details.url;
        }
    },
    { urls: ["<all_urls>"] },
    ["requestBody"]
);

// Listener for request headers
chrome.webRequest.onBeforeSendHeaders.addListener(
    (details) => {
        if (details.method === "POST" && /license/i.test(details.url)) {
            // Extract headers into a more convenient format (e.g., as a key-value object)
            const headers = details.requestHeaders.reduce((acc, header) => {
                acc[header.name] = header.value;
                return acc;
            }, {});
            headerString = "";
            // If you want to append headers to the cURL command, format them accordingly
            for (const name in headers) {
                headerString += ` -H '${name}: ${headers[name]}'`;
            }

            console.log("Matched Request Headers:", headers);
            console.log("cURL headers part:", headerString);
            // You might also want to combine this with your earlier cURL command
        }
    },
    { urls: ["<all_urls>"] },
    // Make sure to include "requestHeaders" (and "extraHeaders" if needed)
    ["requestHeaders", "extraHeaders"]
);

function curlCommand()
{
    return `curl '${licenseUrl}' ${headerString}   --data-raw $'${licenseData}'`;
}


chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (msg.action === "updateTitle" && msg.title) {
        title = msg.title;  // update your stored title variable
        console.log("Automatically extracted title:", title);
    }
});

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (msg.action === "getTitle") {
        sendResponse({ title: title }); // 'title' is your stored title variable
    }
    // Don't forget to return true if you plan to send the response asynchronously
});
// Listen for messages from the popup (button click)
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (msg.action === "sendData") {
        // Create an object with both parameters.
        const dataToSend = {
            manifestUrl: manifestUrl,   // GET request URL
            licenseCurl: curlCommand(),    // POST cURL command
            title: msg.title              // The title from the popup
        };
        console.log("Curl command:", curlCommand());

        // Send the collected data to the native host
        chrome.runtime.sendNativeMessage(
            "org.hellyes.hellyes", // This must match the "name" in your native messaging host manifest
            dataToSend,
            (response) => {
                if (chrome.runtime.lastError) {
                    console.error("Error sending native message:", chrome.runtime.lastError.message);
                    sendResponse({ status: "error", error: chrome.runtime.lastError.message });
                } else {
                    console.log("Native host responded:", response);
                    sendResponse({ status: "success", response: response });
                }
            }
        );

        // Clear the stored values after sending if desired
        return true; // Indicate asynchronous response
    }
});
