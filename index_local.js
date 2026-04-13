// index.js
const express = require('express');
const fs = require('fs');
const path = require('path');

// Initialize Express app
const app = express();
const PORT = 3000; 

// --- Data Loading Function (Simulates Database Connection) ---
function loadCalendarData() {
    try {
        const filePath = path.join(__dirname, 'data', 'calendar_data.json');
        console.log(`[INFO] Loading data from: ${filePath}`);
        return JSON.parse(fs.readFileSync(filePath, 'utf8'));
    } catch (error) {
        console.error("[FATAL ERROR] Could not load calendar data:", error);
        return null; // Return null on fatal failure
    }
}

const calendarData = loadCalendarData();


// --- The Universal API Endpoint ---
/**
 * GET /api/lookup?date=<DATE>&source=gregorian OR hijri
 * Examples: 
 * 1. http://localhost:3000/api/lookup?date=2025-01-03&source=gregorian 
 * 2. http://localhost:3000/api/lookup?date=1446-07-03&source=hijri
 */
app.get('/api/lookup', (req, res) => {
    // Get inputs from the URL query parameters
    const requestedDate = req.query.date;
    const sourceType = req.query.source;

    // 1. Input Validation Check
    if (!requestedDate || !sourceType) {
        console.warn("[ATTEMPT] Missing required parameters.");
        return res.status(400).json({
            success: false,
            error: "Missing parameters.",
            message: "You must provide both 'date' and 'source'.",
            usage: "Example: http://localhost:3000/api/lookup?date=2025-01-03&source=gregorian"
        });
    }

    // 2. Determine which lookup map to use based on the source type
    let lookupMap;
    if (sourceType === 'gregorian') {
        lookupMap = calendarData.gregorian_to_hijri;
    } else if (sourceType === 'hijri') {
        lookupMap = calendarData.hijri_to_gregorian;
    } else {
        return res.status(400).json({
            success: false,
            error: "Invalid source type.",
            message: "The source must be either 'gregorian' or 'hijri'."
        });
    }

    // 3. Perform the Lookup
    const foundOppositeDate = lookupMap[requestedDate];

    if (foundOppositeDate) {
        // Data Found: Compile the comprehensive response
        const responseJson = {
            success: true,
            input_data: {
                date: requestedDate,
                type: sourceType.toUpperCase(), // e.g., GREGORIAN
            },
            output_data: {
                date: foundOppositeDate,
                type: (sourceType === 'gregorian' ? 'HIJRI' : 'GREGORIAN'), 
            },
            message: "Conversion successful.",
            // Add any meta-data here if needed later
        };
        res.status(200).json(responseJson);

    } else {
        // Data Not Found
        console.warn(`[MISSING] No data found for ${requestedDate} (${sourceType})`);
        const errorResponse = {
            success: false,
            input_data: {
                date: requestedDate,
                type: sourceType.toUpperCase(),
            },
            error: "Data not found.",
            message: `No calendar pair exists for ${requestedDate} (${sourceType}).`,
        };
        res.status(404).json(errorResponse);
    }
});


// Start the server
app.listen(PORT, () => {
    console.log(`===========================================`);
    console.log(`✅ Calendar Lookup API running successfully on port ${PORT}`);
    console.log(`Test 1 (GREGORIAN -> HIJRI): http://localhost:${PORT}/api/lookup?date=2025-01-03&source=gregorian`);
    console.log(`Test 2 (HIJRI -> GREGORIAN): http://localhost:${PORT}/api/lookup?date=1446-07-03&source=hijri`);
    console.log(`===========================================`);
});

