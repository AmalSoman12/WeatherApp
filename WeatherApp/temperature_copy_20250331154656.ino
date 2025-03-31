// Define the analog pin connected to LM35 output
const int lm35Pin = A0;

void setup() {
  // Initialize serial communication at 9600 baud rate
  Serial.begin(9600);
}

void loop() {
  // Read the analog value from LM35 (0 to 1023)
  int sensorValue = analogRead(lm35Pin);

  // Convert the analog value to voltage (Arduino uses 5V reference)
  float voltage = sensorValue * (5.0 / 1023.0);

  // Convert voltage to temperature in Celsius (LM35: 10mV per °C)
  float temperatureC = voltage * 100.0;

  // Print the temperature to the Serial Monitor
  Serial.print("Current temperature: ");
  Serial.print(temperatureC);
  Serial.println("°C");

  // Wait for 1 second before the next reading
  delay(1000);
}