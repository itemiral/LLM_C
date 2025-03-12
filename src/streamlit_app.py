import streamlit as st
import requests
import folium
from streamlit_folium import folium_static  # Use folium_static instead of st_folium
from folium import Icon
import numpy as np
import openai
import os
import math

# Initialize OpenAI client with default API key
openai.api_key = os.getenv('OPENAI_API_KEY')

st.title("🎈 WindBorne Balloon Tracker")

# Define the API URL of the Flask backend
API_URL = "http://127.0.0.1:5000/analyze"

# Check if there is any existing data in session state
if 'data' not in st.session_state:
    st.session_state.data = None

# Fetch data from Flask API
if st.button("Fetch Balloon Data"):
    st.write("Fetching latest balloon data...")
    try:
        response = requests.get(API_URL)  # Fetching data from the Flask backend
        response.raise_for_status()  # Raise an exception for invalid responses
        data = response.json()

        if 'balloon_data' in data:
            balloon_data = data['balloon_data']

            # Displaying map and data analysis
            mean_altitude = np.mean([d[2] for d in balloon_data])
            st.write(f"📊 **Mean Altitude:** {mean_altitude:.2f}m")

            # Initialize Map
            m = folium.Map(location=[0, 0], zoom_start=2)

            # Add markers for each balloon
            balloon_icon = Icon(color="blue", icon="cloud", icon_color="white")
            for lat, lon, alt in balloon_data:
                folium.Marker([lat, lon], popup=f"Altitude: {alt}m", icon=balloon_icon).add_to(m)

            # Display map using folium_static
            folium_static(m, width=1800, height=1000)

    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch data: {e}")
