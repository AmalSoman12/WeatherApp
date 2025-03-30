from flask import Flask, render_template, request, jsonify
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import numpy as np
from datetime import datetime
import serial
import threading
import time

app = Flask(__name__)

# Constants
DEFAULT_TEMP_C = 26.7
DEFAULT_TEMP_F = (DEFAULT_TEMP_C * 9/5) + 32

# Global variable to store the latest temperature
latest_temp = None
sensor_active = False


def read_serial():
    """
    Reads temperature data from the Arduino via Serial communication.
    Updates the global `latest_temp` variable with the received temperature.
    """
    global latest_temp, sensor_active
    while True:
        try:
            ser = serial.Serial('COM3', 9600, timeout=1)  # Change COM3 to your Arduino's port
            sensor_active = True
            while True:
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8').strip()
                    if line.startswith("Temperature:"):
                        try:
                            latest_temp = float(line.split(" ")[1])
                        except ValueError:
                            pass
            time.sleep(2)
        except Exception as e:
            sensor_active = False
            print(f"Serial error: {e}")
            time.sleep(5)  # Wait before retrying

# Start serial reading thread
serial_thread = threading.Thread(target=read_serial, daemon=True)
serial_thread.start()

# Load and prepare data
df = pd.read_csv('seattle-weather.csv')
df['date'] = pd.to_datetime(df['date'])
df['month'] = df['date'].dt.month # Extract month from date
df['day_of_year'] = df['date'].dt.dayofyear # Extract day of the year

# Encode weather labels
le = LabelEncoder()
df['weather_encoded'] = le.fit_transform(df['weather'])  # Convert weather labels to numerical values

# Train the Random Forest model
features = ['precipitation', 'temp_max', 'temp_min', 'wind', 'month', 'day_of_year']
target = 'weather_encoded'
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(df[features], df[target])

@app.route('/')
def home():
    """
    Renders the homepage (index.html).
    """
    return render_template('index.html')

@app.route('/get_temp', methods=['GET'])
def get_temp():
    """
    Returns the latest temperature reading from the sensor.
    If the sensor is not active, it returns the default temperature (26.7°C or 80°F).
    """
    global latest_temp, sensor_active
    try:
        if sensor_active and latest_temp is not None:
            return jsonify({
                'temp': latest_temp,
                'source': 'sensor' # Indicates that the temperature is from the sensor
            })
        else:
            return jsonify({
                'temp': DEFAULT_TEMP_F,   # Returns the default temperature in Fahrenheit
                'source': 'default' # Indicates that the default value is being used
            })
    except Exception as e:
        print(f"Error getting temperature: {e}")
        return jsonify({
            'temp': DEFAULT_TEMP_F,
            'source': 'default'
        })

@app.route('/predict', methods=['POST'])
def predict():
    """
    Receives weather input data via a POST request, processes it,
    and returns a weather prediction using the trained Random Forest model.
    """
    try:
        data = request.get_json()  # Get input data from JSON request
        
        # Parse the provided date
        date = datetime.strptime(data['date'], '%Y-%m-%d')
        month = date.month
        day_of_year = date.timetuple().tm_yday
        
        # Prepare input features for prediction
        features = [
            float(data['precipitation']),
            float(data['temp_max']),
            float(data['temp_min']),
            float(data['wind']),
            month,
            day_of_year
        ]
        
        # Make a weather predictio  
        prediction = model.predict([features])[0]
        weather = le.inverse_transform([prediction])[0] # Convert back to readable label
        
        return jsonify({
            'status': 'success',
            'prediction': weather,
            'details': get_weather_details(weather) # Get a descriptive message about the predicted weather
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

def get_weather_details(weather):
    """
    Returns a descriptive message based on the predicted weather condition.
    """
    details = {
        'rain': 'Expect wet conditions. Don\'t forget your umbrella!',
        'sun': 'Perfect day to go outside and enjoy the sunshine!',
        'drizzle': 'Light rain expected. A jacket might be useful.',
        'snow': 'Cold with snow possible. Bundle up and drive safely!',
        'fog': 'Reduced visibility expected. Be cautious if driving.'
    }
    return details.get(weather, 'Typical weather conditions expected.')

if __name__ == '__main__':
    """
    Starts the Flask application.
    """
    app.run(debug=True)