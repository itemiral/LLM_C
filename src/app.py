import os
import requests
import json
import numpy as np
from openai import OpenAI
from flask import Flask, jsonify

# Initialize OpenAI client with default API key
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

app = Flask(__name__)

# Function to fetch balloon data with error handling for corrupted/missing files
def fetch_balloon_data():
    data = []
    errors = []  # Keep track of URLs that had issues
    for i in range(24):
        url = f"https://a.windbornesystems.com/treasure/{str(i).zfill(2)}.json"
        try:
            res = requests.get(url)
            res.raise_for_status()  # Will raise an exception for 404s or other errors
            try:
                json_data = res.json()  # Attempt to parse JSON
                if isinstance(json_data, list):
                    data.extend(json_data)
                else:
                    errors.append(f"Warning: Non-list data format at {url}")
            except json.JSONDecodeError as e:
                errors.append(f"Invalid JSON format at {url}: {e}")
        except requests.exceptions.RequestException as e:
            errors.append(f"Error with URL {url}: {e}")
    
    if errors:
        print("\nErrors during data fetching:")
        for error in errors:
            print(error)

    return data

# Function to analyze balloon data
# Function to analyze balloon data
def analyze_flight(balloon_data):
    if not balloon_data:
        return {"mean_altitude": "No Data", "ai_summary": "No flight data available."}

    # Extract altitudes and skip None values, check if valid data exists
    altitudes = []
    valid_data = []  # List to store valid data points
    for b in balloon_data:
        if isinstance(b, list) and len(b) > 2:
            lat, lon, alt = b[0], b[1], b[2]
            # Check if lat, lon, and alt are valid numbers
            if isinstance(lat, (int, float)) and isinstance(lon, (int, float)) and isinstance(alt, (int, float)):
                valid_data.append((lat, lon, alt))  # Only add valid data points
                altitudes.append(alt if not np.isnan(alt) else 0)  # Replace NaN with 0
            else:
                print(f"Invalid data for coordinates: {lat}, {lon}, {alt}")  # Debugging line
        else:
            print(f"Invalid entry: {b}")  # Debugging line

    print(f"Valid data: {valid_data}")  # Debugging line
    print(f"Altitudes: {altitudes}")  # Debugging line

    # Safely calculate mean altitude, handling empty or invalid data
    if altitudes:
        mean_alt = np.mean(altitudes)
    else:
        mean_alt = "No valid altitude data"

    # Generate AI insights using OpenAI
    prompt = f"Summarize this balloon flight data:\n{valid_data[:5]}..."  # Take only the first 5 entries for brevity

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Change to turbo or another model you have access to
            messages=[
                {"role": "system", "content": "You are an expert in analyzing flight patterns."},
                {"role": "user", "content": prompt}
            ]
        )
        ai_summary = response.choices[0].message.content
    except Exception as e:
        ai_summary = f"Error generating summary: {e}"

    # Return only the first mean altitude and AI insights summary
    return {"mean_altitude": mean_alt, "ai_summary": ai_summary, "balloon_data": valid_data}


# API Endpoint to fetch data
@app.route("/analyze", methods=["GET"])
def analyze():
    data = fetch_balloon_data()
    result = analyze_flight(data)
    return jsonify(result)

# API Endpoint to accept POST requests (if needed for AI analysis from frontend)
@app.route("/analyze", methods=["POST"])
def analyze_post():
    # Get the balloon data from the request payload
    data = requests.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Process the balloon data and generate insights
    result = analyze_flight(data)
    
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)
