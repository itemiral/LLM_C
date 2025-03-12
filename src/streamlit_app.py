import streamlit as st
import requests
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static
from folium import Icon
import numpy as np
import openai
import os
import json
import math

# Initialize OpenAI client with default API key
openai.api_key = os.getenv('OPENAI_API_KEY')

# Set Streamlit layout to wide to take up more space on the screen
st.set_page_config(layout="wide")

st.title("🎈 WindBorne Balloon Tracker")

# Define the API URL of the Flask backend
API_URL = "http://127.0.0.1:5000/analyze"

# Check if there is any existing data in session state
if 'data' not in st.session_state:
    st.session_state.data = None

if st.button("Fetch Balloon Data"):
    st.write("Fetching latest balloon data...")

    try:
        responses = []
        for i in range(24):  # Fetch data for each of the 24 hours
            url = f"https://a.windbornesystems.com/treasure/{str(i).zfill(2)}.json"
            try:
                res = requests.get(url)
                res.raise_for_status()  # Will raise an exception for 404s or other errors
                try:
                    json_data = res.json()
                    if isinstance(json_data, list):
                        responses.append({'data': json_data, 'hour': i})
                    else:
                        pass  # Skip invalid data format without warning
                except json.JSONDecodeError:
                    pass  # Skip invalid JSON without warning
            except requests.exceptions.RequestException as e:
                pass  # Skip any request exceptions without warning

        # Flatten the data for all hours into a single list
        balloon_data = []
        for response in responses:
            for data_point in response['data']:
                if len(data_point) == 3:
                    lat, lon, alt = data_point
                    # Substitute NaN values with 0
                    if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
                        # Replace NaN with 0 for altitude and invalid coordinates
                        if isinstance(alt, (int, float)) and not math.isnan(alt):
                            balloon_data.append((lat, lon, alt))
                        else:
                            balloon_data.append((lat, lon, 0))  # Replace NaN altitude with 0
        st.session_state.data = balloon_data[:300]  # Limit to 300 data points for testing

    except requests.exceptions.RequestException as e:
        st.error(f"Failed to reach the API: {e}")

# Check if data is available in session state and display
if st.session_state.data:
    # Debugging: Display the first few data points to ensure correctness
    st.write(f"Fetched Data (first 5 entries): {st.session_state.data[:5]}")

    # Calculate Mean Altitude
    mean_altitude = np.mean([d[2] for d in st.session_state.data])
    st.write(f"📊 **Mean Altitude:** {mean_altitude:.2f}m")

    # Generate AI Insights using OpenAI
    prompt = f"Summarize this balloon flight data:\n{st.session_state.data[:5]}..."  # First 5 data points for brevity

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Use the appropriate OpenAI model
            messages=[
                {"role": "system", "content": "You are an expert in analyzing flight data."},
                {"role": "user", "content": prompt}
            ]
        )
        ai_summary = response['choices'][0]['message']['content']
    except Exception as e:
        ai_summary = f"Error generating summary: {e}"

    st.write(f"🧠 **AI Insights:** {ai_summary}")

    # Initialize the map based on balloon data
    latitudes = [lat for lat, lon, alt in st.session_state.data]
    longitudes = [lon for lat, lon, alt in st.session_state.data]
    
    # Replace NaN values with 0 for latitude and longitude if any are NaN
    latitudes = [lat if not math.isnan(lat) else 0 for lat in latitudes]
    longitudes = [lon if not math.isnan(lon) else 0 for lon in longitudes]
    
    # Calculate the mean lat and lon for the map's center
    mean_lat = np.mean(latitudes)
    mean_lon = np.mean(longitudes)

    # Initialize map centered around the mean latitude and longitude
    m = folium.Map(location=[mean_lat, mean_lon], zoom_start=5)

    # Initialize MarkerCluster
    marker_cluster = MarkerCluster().add_to(m)

    # Create custom balloon icon (No highlight)
    balloon_icon = Icon(color="blue", icon="cloud", icon_color="white")

    # Add markers for each balloon with debugging
    for idx, (lat, lon, alt) in enumerate(st.session_state.data):
        # Debugging: Display each marker's position
        st.write(f"Marker {idx}: Latitude={lat}, Longitude={lon}, Altitude={alt}")

        # Substitute invalid lat or lon with 0 if NaN
        lat = lat if not math.isnan(lat) else 0
        lon = lon if not math.isnan(lon) else 0

        # Create marker and add to the cluster
        marker = folium.Marker([lat, lon], popup=f"Altitude: {alt}m", icon=balloon_icon)
        marker.add_to(marker_cluster)

    # Display the map with the markers
    folium_static(m, width=700)  # Set width for future
