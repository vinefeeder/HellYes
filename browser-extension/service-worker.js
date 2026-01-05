// Object to store data per tab
let tabData = {};

let getProgramInfoHeaders = {};

function storeTabData(tabId, key, value) {
    if (tabId < 0) return; // Ignore requests not associated with a tab
    if (!tabData[tabId]) tabData[tabId] = {};
    tabData[tabId][key] = value;
    console.log(`set ${tabId} key ${key} value ${value}`);

    updateIconForTab(tabId);
}

// Helper: update the extension's icon for a specific tab
function updateIconForTab(tabId) {
    if (tabId < 0) return; // Ensure valid tabId

    const tabInfo = tabData[tabId] || {};
    // Check if both manifestUrl and curlCommand are present
    const hasManifest = !!tabInfo.manifestUrl;
    const hasCurl = !!curlCommand(tabId); // returns non-empty string if all parts are available

    // Determine which icon to use
    const baseIcon = (hasManifest && hasCurl) ? "logo/hellyes.png" : "logo/hellno.png";

    // Provide an object with sizes mapping. Make sure your images are of the correct dimensions!
    const iconPaths = {
        "16": baseIcon,
        "32": baseIcon,
        "48": baseIcon,
        "128": baseIcon,
    };

    chrome.action.setIcon({ path: iconPaths, tabId: tabId }, () => {
        if (chrome.runtime.lastError) {
            console.error(baseIcon);
            console.error("Error setting icon:", chrome.runtime.lastError.message);
        }
    });
}
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (msg.action === "getTabData") {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (tabs.length === 0) return;

            let tabId = tabs[0].id;
            let tabInfo = tabData[tabId] || {};

            sendResponse({
                manifestUrl: tabInfo.manifestUrl || "",
                curlCommand: curlCommand(tabId) || "",
                title: tabInfo.title || ""
            });
        });

        return true; // Indicate async response
    }
});
// Listen for network requests and filter by "manifest" or "license"
chrome.webRequest.onCompleted.addListener(
    (details) => {
        // Only process GET requests
        if (details.method !== "GET") return;

        // Exclude requests that are for images
        if (details.type === "image") return;
        if (/manifest|license/i.test(details.url)) {
            storeTabData(details.tabId, 'manifestUrl', details.url)
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
// Helper: convert raw bytes to Base64
function bytesToBase64(rawBytes) {
    const uint8 = new Uint8Array(rawBytes);
    let binary = "";
    for (let i = 0; i < uint8.length; i++) {
        binary += String.fromCharCode(uint8[i]);
    }
    return btoa(binary);
}

chrome.webRequest.onBeforeRequest.addListener(
    (details) => {
        if (details.method === "POST" && /license/i.test(details.url)) {

            let tabId = details.tabId;
            if (tabId < 0) return;

            let dataStr = "";

            if (details.requestBody) {
                if (details.requestBody.raw && details.requestBody.raw.length > 0) {
                    // For binary data, do not assume UTF-8; convert to escaped hex
                    dataStr = bytesToEscapedString(details.requestBody.raw[0].bytes);
                    base64Str = bytesToBase64(details.requestBody.raw[0].bytes);
                } else if (details.requestBody.formData) {
                    // For form data, you could JSON-stringify it or build key=value pairs
                    dataStr = JSON.stringify(details.requestBody.formData);
                    base64Str = JSON.stringify(details.requestBody.formData);
                }
            }
            storeTabData(tabId, 'licenseData', dataStr)
            storeTabData(tabId, 'licenseBase64', base64Str)
            storeTabData(tabId, 'licenseUrl', details.url)
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

            let tabId = details.tabId;
            if (tabId < 0) return;

            let headerString = "";
            // If you want to append headers to the cURL command, format them accordingly
            for (const name in headers) {
                // Use double quotes for Windows compatibility
                const escapedValue = headers[name].replace(/"/g, '\\"');
                headerString += ` -H "${name}: ${escapedValue}"`;
            }
            storeTabData(tabId, 'headers', headers); // Store the raw headers object
            storeTabData(tabId, 'headerString', headerString)
            console.log("Matched Request Headers:", headers);
            console.log("cURL headers part:", headerString);
        }
    },
    { urls: ["<all_urls>"] },
    // Make sure to include "requestHeaders" (and "extraHeaders" if needed)
    ["requestHeaders"]
);

function curlCommand(tabId) {
    if (!tabData[tabId]) return "";

    const tabInfo = tabData[tabId]; // Ensure the object exists
    const licenseUrl = tabInfo.licenseUrl || "";
    const headerString = tabInfo.headerString || "";
    const licenseData = tabInfo.licenseData || "";
    const licenseBase64 = tabInfo.licenseBase64 || "";

    // Return empty string if any of them are missing
    if (!licenseUrl || !headerString || !licenseData) {
        return "";
    }

    // Windows-compatible: use double quotes and escape backslashes and quotes
    const escapedData = licenseData.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
    return `curl "${licenseUrl}" ${headerString} --data-raw "${escapedData}"`;
}





chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (msg.action === "updateTitle" && msg.title && sender.tab) {
        storeTabData(sender.tab.id, "title", msg.title);
        console.log(`[Tab ${sender.tab.id}] Automatically extracted title:`, msg.title);
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
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (tabs.length === 0) {
                console.error("No active tabs found.");
                sendResponse({ status: "error", error: "No active tab found" });
                return;
            }

            let tabId = tabs[0].id;

            if (!tabData[tabId]) {
                console.error(`No data stored for tabId ${tabId}`);
                sendResponse({ status: "error", error: "No data available for this tab" });
                return;
            }

            // Create an object with the necessary parameters for allhell3.py
            const dataToSend = {
                manifestUrl: tabData[tabId].manifestUrl || "",
                licenseUrl: tabData[tabId].licenseUrl || "",
                bodyBase64: tabData[tabId].licenseBase64 || "", // The script expects bodyBase64
                headers: tabData[tabId].headers || {},          // The script expects a dict
                title: msg.title || tabData[tabId].title || "video", // Prioritize user input
                deleteMe: false
            };

            console.log("Sending data to native host:", dataToSend);

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

            return true; // Indicate asynchronous response
        });

        return true; // Indicate asynchronous response
    }
});

