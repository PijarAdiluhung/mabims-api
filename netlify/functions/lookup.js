// index.js - Adapted for Netlify Serverless Function environment

const fs = require("fs");
const path = require("path");

// --- Data Loading Function (Stays the same) ---
function loadCalendarData() {
  try {
    // We use `path.join(process.cwd(), ...)` to ensure we always start from the root of the project,
    // regardless of where the function is placed.
    const filePath = path.join(process.cwd(), "data", "calendar_data.json");
    console.log(`[INFO] Loading data from: ${filePath}`);
    return JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch (error) {
    console.error("[FATAL ERROR] Could not load calendar data:", error);
    // Use null or an empty object to prevent the function from crashing entirely
    return null;
  }
}

const calendarData = loadCalendarData();

/**
 * Main Lookup Function - This is what Netlify will execute.
 * @param {object} event - Contains query parameters (e.g., date, source).
 */
exports.handler = async (event) => {
  if (!calendarData) {
    console.error("API FAILURE: Calendar data failed to load at startup.");
    return {
      statusCode: 503, // Use 503 Service Unavailable
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

  // 1. Input Validation Check
  if (!requestedDate || !sourceType) {
    return {
      // Netlify functions return a JSON object that Express would send
      statusCode: 400,
      body: {
        success: false,
        error: "Missing parameters.",
        message: "You must provide both 'date' and 'source'.",
        usage: "Example: ?date=2025-01-03&source=gregorian",
      },
    };
  }

  // 2. Determine which lookup map to use
  let lookupMap;
  if (sourceType === "gregorian") {
    lookupMap = calendarData.gregorian_to_hijri;
  } else if (sourceType === "hijri") {
    lookupMap = calendarData.hijri_to_gregorian;
  } else {
    return {
      statusCode: 400,
      body: JSON.stringify({
        success: false,
        error: "Invalid source type.",
        message: "The source must be either 'gregorian' or 'hijri'.",
      }),
    };
  }

  // 3. Perform the Lookup
  const foundOppositeDate = lookupMap[requestedDate];

  if (foundOppositeDate) {
    // Data Found: Compile and return success JSON
    return {
      statusCode: 200,
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
    // Data Not Found
    return {
      statusCode: 404,
      body: JSON.stringify({
        success: false,
        input_data: { date: requestedDate, type: sourceType.toUpperCase() },
        error: "Data not found.",
        message: `No calendar pair exists for ${requestedDate} (${sourceType}).`,
      }),
    };
  }
};
