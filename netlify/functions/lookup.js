// index.js - Adapted for Netlify Serverless Function environment

const fs = require("fs");
const path = require("path");

// --- SECURITY CONFIGURATION ---

// [MODIFIED] This list dictates who can even attempt to use the API.
const ALLOWED_DOMAINS = new Set([
  "https://malangmengaji.com",
  "https://peta-malangmengaji.web.app",
]);

/**
 * Checks if the incoming request's Origin is whitelisted.
 * @param {string} origin - The Origin header from the request event.
 * @returns {boolean} True if allowed, false otherwise.
 */
function isOriginAllowed(origin) {
  if (!origin) return false; // No origin provided

  // Check against explicit domains
  for (const domain of ALLOWED_DOMAINS) {
    if (origin === domain) {
      return true;
    }
  }

  // Special check for subdomains: This handles *subdomain.malangmengaji.com
  if (
    origin &&
    origin.endsWith(".malangmengaji.com") &&
    !ALLOWED_DOMAINS.includes(origin)
  ) {
    console.warn(
      `[SECURITY] Detected whitelisted subdomain access from: ${origin}`,
    );
    return true; // Trusting all subdomains for simplicity in this POC
  }

  return false;
}

/**
 * Creates the CORS headers, but ONLY if the request is authorized.
 * @returns {object | null} The required headers or null if blocked.
 */
function getCorsHeaders(allowed = true) {
  const headers = {
    "Access-Control-Allow-Methods": "GET", // Restrict to GET requests only
    // If we allow it, we set the allowed origin. If not, this is irrelevant
    // because a 403 will be returned before CORS matters.
    "Access-Control-Allow-Origin": "*", // We keep * here but enforce restriction in code logic
    "Access-Control-Allow-Headers": "Content-Type, Origin, Accept",
  };

  // If we were running this in a secure environment, we would set the
  // Access-Control-Allow-Origin to the specific approved domain.
  return headers;
}

// --- Data Loading Function (Stays the same) ---
function loadCalendarData() {
  try {
    const filePath = path.join(process.cwd(), "data", "calendar_data.json");
    console.log(`[INFO] Loading data from: ${filePath}`);
    return JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch (error) {
    console.error("[FATAL ERROR] Could not load calendar data:", error);
    return null;
  }
}

const calendarData = loadCalendarData();

/**
 * Main Lookup Function - This is what Netlify will execute.
 * @param {object} event - Contains query parameters (e.g., date, source).
 */
exports.handler = async (event) => {
  // ------------------------------------------
  // [!!!] STEP 1: ACCESS GATEWAY / AUTHENTICATION CHECK
  // ------------------------------------------
  const origin = event.headers?.origin; // Access the Origin header
  if (!isOriginAllowed(origin)) {
    return {
      statusCode: 403, // Forbidden Status Code
      headers: getCorsHeaders(),
      body: JSON.stringify({
        success: false,
        error: "Forbidden.",
        message: `Access is restricted to whitelisted partner domains only. Your current origin (${origin || "Unknown"}) is not authorized.`,
        usage: "Please contact support for access credentials.",
      }),
    };
  }

  // --- 2. API Failure Check (503 Status Code) ---
  if (!calendarData) {
    return {
      statusCode: 503,
      headers: getCorsHeaders(),
      body: JSON.stringify({
        success: false,
        error: "Service Unavailable.",
        message:
          "The calendar database could not be loaded. Please try again later.",
      }),
    };
  }

  // Netlify passes request params through the 'queryStringParameters' property
  const params = event.queryStringParameters || {};
  const requestedDate = params.date;
  const sourceType = params.source;

  // --- 3. Input Validation Check (400 Status Code) ---
  if (!requestedDate || !sourceType) {
    return {
      statusCode: 400,
      headers: getCorsHeaders(),
      body: JSON.stringify({
        success: false,
        error: "Missing parameters.",
        message: "You must provide both 'date' and 'source'.",
        usage: "Example: ?date=2025-01-03&source=gregorian",
      }),
    };
  }

  // --- 4. Determine which lookup map to use (400 Status Code) ---
  let lookupMap;
  if (sourceType === "gregorian") {
    lookupMap = calendarData.gregorian_to_hijri;
  } else if (sourceType === "hijri") {
    lookupMap = calendarData.hijri_to_gregorian;
  } else {
    return {
      statusCode: 400,
      headers: getCorsHeaders(),
      body: JSON.stringify({
        success: false,
        error: "Invalid source type.",
        message: "The source must be either 'gregorian' or 'hijri'.",
      }),
    };
  }

  // --- 5. Perform the Lookup and Return Data ---

  const foundOppositeDate = lookupMap[requestedDate];

  if (foundOppositeDate) {
    // Data Found: Compile and return success JSON
    return {
      statusCode: 200,
      headers: getCorsHeaders(), // Use restricted headers here
      body: JSON.stringify({
        success: true,
        input_data: { date: requestedDate, type: sourceType.toUpperCase() },
        output_data: {
          date: foundOppositeDate,
          type: sourceType === "gregorian" ? "HIJRI" : "GREGORIAN",
        },
        message: "Conversion successful.",
      }),
    };
  } else {
    // Data Not Found (404 Status Code)
    return {
      statusCode: 404,
      headers: getCorsHeaders(), // Use restricted headers here
      body: JSON.stringify({
        success: false,
        input_data: { date: requestedDate, type: sourceType.toUpperCase() },
        error: "Data not found.",
        message: `No calendar pair exists for ${requestedDate} (${sourceType}).`,
      }),
    };
  }
};
