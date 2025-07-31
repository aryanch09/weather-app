import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import os

if os.getenv("STREAMLIT_SERVER") is None:
    from dotenv import load_dotenv
    load_dotenv()

try:
    API_KEY = st.secrets['OPENWEATHER_API_KEY']
except KeyError:
    API_KEY = os.getenv('OPENWEATHER_API_KEY')

if not API_KEY:
    st.error("API key not found. Please set the OPENWEATHER_API_KEY environment variable or Streamlit secret.")
    st.stop()

WEATHER_URL = "http://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "http://api.openweathermap.org/data/2.5/forecast"

st.set_page_config(layout="wide")
st.title("🌤️ Weather Dashboard")

city = st.text_input("Enter a city name:")

if city:
    params = {"q": city, "appid": API_KEY, "units": "metric"}

    weather_res = requests.get(WEATHER_URL, params=params)
    forecast_res = requests.get(FORECAST_URL, params=params)

    if weather_res.status_code == 200 and forecast_res.status_code == 200:
        weather = weather_res.json()
        forecast = forecast_res.json()

        temp = weather["main"]["temp"]
        humidity = weather["main"]["humidity"]
        wind_speed = weather["wind"]["speed"]
        description = weather["weather"][0]["description"].capitalize()
        country = weather["sys"]["country"]
        city_name = weather["name"]

        # Build forecast DataFrame
        forecast_list = forecast["list"]
        df = pd.DataFrame([{
            "Datetime": entry["dt_txt"],
            "Temp": entry["main"]["temp"],
            "Temp_Min": entry["main"]["temp_min"],
            "Temp_Max": entry["main"]["temp_max"]
        } for entry in forecast_list])

        df["Datetime"] = pd.to_datetime(df["Datetime"])
        df["Date"] = df["Datetime"].dt.date
        df["Temp_F"] = df["Temp"] * 9 / 5 + 32
        df["Temp_Min_F"] = df["Temp_Min"] * 9 / 5 + 32
        df["Temp_Max_F"] = df["Temp_Max"] * 9 / 5 + 32

        # Prepare daily min/max summary
        daily_summary = df.groupby("Date").agg({
            "Temp_Min": "min",
            "Temp_Max": "max",
            "Temp_Min_F": "min",
            "Temp_Max_F": "max"
        }).reset_index()

        col1, col2 = st.columns([1, 2])

        with col1:
            st.subheader(f"📍 Weather in {city_name}, {country}")
            st.markdown(f"**🌡️ Temperature:** {temp:.1f}°C / {(temp * 9/5 + 32):.1f}°F")
            st.markdown(f"**☁️ Condition:** {description}")
            st.markdown(f"**💧 Humidity:** {humidity}%")
            st.markdown(f"**🌬️ Wind Speed:** {wind_speed} m/s")

            # Show daily min/max temps nicely formatted
            st.markdown("### 📅 Daily Min/Max Temperatures")
            for idx, row in daily_summary.iterrows():
                date_str = row["Date"].strftime("%A, %b %d")
                st.markdown(
                    f"**{date_str}**: Min {row['Temp_Min']:.1f}°C / {row['Temp_Min_F']:.1f}°F — "
                    f"Max {row['Temp_Max']:.1f}°C / {row['Temp_Max_F']:.1f}°F"
                )

            # Alerts if any
            alerts = forecast.get("alerts", [])
            if alerts:
                for alert in alerts:
                    st.error(f"🚨 {alert['event']}: {alert['description']}")

        with col2:
            tabs = st.tabs(["Celsius (°C)", "Fahrenheit (°F)"])

            # Celsius graph
            with tabs[0]:
                fig_c = go.Figure()
                fig_c.add_trace(go.Scatter(
                    x=df["Datetime"], y=df["Temp"], mode="lines+markers", name="Temp (°C)",
                    line=dict(color="firebrick")
                ))
                fig_c.add_trace(go.Scatter(
                    x=df["Datetime"], y=df["Temp_Min"], mode="lines", name="Min Temp (°C)",
                    line=dict(color="royalblue", dash="dash")
                ))
                fig_c.add_trace(go.Scatter(
                    x=df["Datetime"], y=df["Temp_Max"], mode="lines", name="Max Temp (°C)",
                    line=dict(color="orange", dash="dash")
                ))
                fig_c.update_layout(
                    title="5-Day Forecast - Celsius",
                    xaxis_title="Date & Time",
                    yaxis_title="Temperature (°C)",
                    hovermode="x unified",
                    legend=dict(y=1, x=0)
                )
                st.plotly_chart(fig_c, use_container_width=True)

            # Fahrenheit graph
            with tabs[1]:
                fig_f = go.Figure()
                fig_f.add_trace(go.Scatter(
                    x=df["Datetime"], y=df["Temp_F"], mode="lines+markers", name="Temp (°F)",
                    line=dict(color="firebrick")
                ))
                fig_f.add_trace(go.Scatter(
                    x=df["Datetime"], y=df["Temp_Min_F"], mode="lines", name="Min Temp (°F)",
                    line=dict(color="royalblue", dash="dash")
                ))
                fig_f.add_trace(go.Scatter(
                    x=df["Datetime"], y=df["Temp_Max_F"], mode="lines", name="Max Temp (°F)",
                    line=dict(color="orange", dash="dash")
                ))
                fig_f.update_layout(
                    title="5-Day Forecast - Fahrenheit",
                    xaxis_title="Date & Time",
                    yaxis_title="Temperature (°F)",
                    hovermode="x unified",
                    legend=dict(y=1, x=0)
                )
                st.plotly_chart(fig_f, use_container_width=True)

    else:
        st.error("City not found. Please check spelling and try again.")
