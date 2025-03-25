from flask import Flask, render_template, request, jsonify
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import numpy as np
from datetime import datetime

app = Flask(__name__)

# Load and prepare data
df = pd.read_csv('seattle-weather.csv')
df['date'] = pd.to_datetime(df['date'])
df['month'] = df['date'].dt.month
df['day_of_year'] = df['date'].dt.dayofyear

# Encode weather labels
le = LabelEncoder()
df['weather_encoded'] = le.fit_transform(df['weather'])

# Train model
features = ['precipitation', 'temp_max', 'temp_min', 'wind', 'month', 'day_of_year']
target = 'weather_encoded'
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(df[features], df[target])

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        
        # Parse date
        date = datetime.strptime(data['date'], '%Y-%m-%d')
        month = date.month
        day_of_year = date.timetuple().tm_yday
        
        # Prepare features
        features = [
            float(data['precipitation']),
            float(data['temp_max']),
            float(data['temp_min']),
            float(data['wind']),
            month,
            day_of_year
        ]
        
        # Make prediction
        prediction = model.predict([features])[0]
        weather = le.inverse_transform([prediction])[0]
        
        return jsonify({
            'status': 'success',
            'prediction': weather,
            'details': get_weather_details(weather)
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

def get_weather_details(weather):
    details = {
        'rain': 'Expect wet conditions. Don\'t forget your umbrella!',
        'sun': 'Perfect day to go outside and enjoy the sunshine!',
        'drizzle': 'Light rain expected. A jacket might be useful.',
        'snow': 'Cold with snow possible. Bundle up and drive safely!',
        'fog': 'Reduced visibility expected. Be cautious if driving.'
    }
    return details.get(weather, 'Typical weather conditions expected.')

if __name__ == '__main__':
    app.run(debug=True)