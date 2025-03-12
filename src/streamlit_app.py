import streamlit as st
import requests
import folium
from folium import Icon
from streamlit_folium import folium_static
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

# Check if there is any existing data in session state
if 'data' not in st.session_state:
    st.session_state.data = None

if st.button("Fetch Balloon Data"):
    st.write("Fetching latest balloon data...")

    with st.spinner('Loading data...'):
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

            st.session_state.data = balloon_data[:200]  # Limit to 200 data points

        except requests.exceptions.RequestException as e:
            st.error(f"Failed to reach the API: {e}")

# Check if data is available in session state and display
if st.session_state.data:
    # Calculate Mean Altitude
    mean_altitude = np.mean([d[2] for d in st.session_state.data])
    st.write(f"📊 **Mean Altitude:** {mean_altitude:.2f}m")

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
    m = folium.Map(location=[mean_lat, mean_lon], zoom_start=8)

    # Create markers using CircleMarker for visibility
    for lat, lon, alt in st.session_state.data:
        lat = lat if not math.isnan(lat) else 0
        lon = lon if not math.isnan(lon) else 0

        # Create a simple CircleMarker for each balloon with increased radius for visibility
        marker = folium.CircleMarker(
            location=[lat, lon],
            radius=10,  # Increase radius for bigger markers
            color="blue",
            fill=True,
            fill_color="blue",
            fill_opacity=0.6,
            popup=f"Altitude: {alt}m\nLatitude: {lat}\nLongitude: {lon}"
        )
        
        # Add marker to the map
        marker.add_to(m)

    # Display the map with the markers
    folium_static(m, width=700)  # Set width for future

    # Optionally, add a dropdown to simulate the interaction of clicking on a balloon
    balloon_data = st.session_state.data
    marker_info = st.selectbox("Select a balloon to get insights", balloon_data)
    
    if marker_info:
        lat, lon, alt = marker_info
        st.write(f"Fetching insights for Balloon at Lat: {lat}, Lon: {lon}, Alt: {alt}m")

        # Generate AI Insights for the selected balloon
        prompt = f"Analyze the following balloon data point: Latitude: {lat}, Longitude: {lon}, Altitude: {alt}."

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

        st.write(f"🧠 **AI Insights for Selected Balloon:** {ai_summary}")
