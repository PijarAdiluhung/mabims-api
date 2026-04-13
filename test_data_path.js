// --- Temporary Test File: test_data_path.js ---

const fs = require('fs');
const path = require('path');

function loadCalendarData() {
    console.log("--- Attempting to Load Data ---");
    
    // 1. This is the EXACT path we want to test (the one that failed)
    const filePath = path.join(process.cwd(), 'data', 'calendar_data.json');

    try {
        // 2. Check if the file exists at the calculated path
        if (!fs.existsSync(filePath)) {
            throw new Error(`File not found at: ${filePath}`);
        }

        console.log("[SUCCESS] File located and readable!");
        const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
        return data; 

    } catch (error) {
        // This will tell us exactly WHY the path failed.
        console.error("\n===============================");
        console.error("[FAILURE] Path Test Failed:", error.message);
        console.error("===============================\n");
        return null;
    }
}

const data = loadCalendarData();

if (data) {
    console.log("\n✅ Data successfully loaded!");
    // Print a key piece of data to confirm the object structure is good
    console.log("Example check: gregorian_to_hijri keys:", Object.keys(data.gregorian_to_hijri).slice(0, 5), "...");
} else {
    console.log("\n❌ Data loading failed during local test.");
}
