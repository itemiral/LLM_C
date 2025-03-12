import React, { useState, useEffect } from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import MarkerClusterGroup from "react-leaflet-markercluster";
import L from "leaflet";
import axios from "axios";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

const Card = ({ children }) => <div className="border p-4 rounded-lg shadow-md">{children}</div>;
const CardContent = ({ children }) => <div>{children}</div>;

// Define a custom balloon icon
const balloonIcon = new L.Icon({
  iconUrl: "https://cdn-icons-png.flaticon.com/512/684/684908.png", // Example balloon icon URL
  iconSize: [30, 30],
  iconAnchor: [15, 30],
  popupAnchor: [1, -30],
});

export default function BalloonDashboard() {
  const [balloonData, setBalloonData] = useState([]);
  const [altitudeHistory, setAltitudeHistory] = useState([]);
  const [aiInsights, setAiInsights] = useState("Loading AI insights...");

  useEffect(() => {
    const fetchBalloonData = async () => {
      try {
        const responses = await Promise.all(
          Array.from({ length: 24 }, (_, i) =>
            axios.get(`/treasure/${String(i).padStart(2, "0")}.json`)
            .then((res) => ({ data: res.data, hour: i }))
            .catch((error) => {
              if (error.response?.status === 404) {
                console.log(`Hour ${i}: returned 404`);
              } else {
                console.log(`Hour ${i}: corrupted`);
              }
              return null;
            })
          )
        );

        const validData = responses.filter((entry) => entry && Array.isArray(entry.data));
        const flatData = validData.map((entry) => entry.data.map(d => ({ lat: d[0], lon: d[1], altitude: d[2], hour: entry.hour }))).flat();
        setBalloonData(flatData);
      } catch (error) {
        console.error("Error fetching balloon data", error);
      }
    };

    fetchBalloonData();
  }, []);

  useEffect(() => {
    if (!balloonData.length) return;
    const altHistory = balloonData.filter((_, index) => index % 10 === 0) // Downsample data
      .map(({ hour, altitude }) => ({ hour, altitude }));
    setAltitudeHistory(altHistory);
  }, [balloonData]);

  useEffect(() => {
    if (!balloonData.length) return;
    fetch("http://127.0.0.1:5000/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(balloonData),
    })
    .then(response => response.json())
    .then(data => {
      console.log("AI Analysis:", data);
      setAiInsights(data.ai_summary);
    })
    .catch(error => console.error("Error fetching AI insights:", error));
  }, [balloonData]);

  return (
    <div className="flex flex-col gap-4 p-4">
      <h1 className="text-2xl font-bold">Live Balloon Flight & Weather Dashboard</h1>
      <MapContainer center={[20, 0]} zoom={2} style={{ height: "500px", width: "100%" }}>
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <MarkerClusterGroup>
          {balloonData.slice(0, 500).map((balloon, index) => (
            <Marker key={index} position={[balloon.lat, balloon.lon]} icon={balloonIcon}>
              <Popup>
                <strong>Altitude:</strong> {balloon.altitude.toFixed(2)}m
              </Popup>
            </Marker>
          ))}
        </MarkerClusterGroup>
      </MapContainer>
      <Card>
        <CardContent>
          <h2 className="text-lg font-semibold">Altitude History (Last 24H)</h2>
          {altitudeHistory.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={altitudeHistory}>
                <XAxis dataKey="hour" label={{ value: "Hour", position: "insideBottomRight" }} />
                <YAxis label={{ value: "Altitude (m)", angle: -90, position: "insideLeft" }} />
                <Tooltip />
                <Line type="monotone" dataKey="altitude" stroke="#8884d8" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p>No altitude data available</p>
          )}
        </CardContent>
      </Card>
      <Card>
        <CardContent>
          <h2 className="text-lg font-semibold">AI-Generated Insights</h2>
          <p>{aiInsights}</p>
        </CardContent>
      </Card>
    </div>
  );
}