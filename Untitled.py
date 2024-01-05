import firebase_admin
from firebase_admin import credentials, db
import time

# Initialize Firebase
cred = credentials.Certificate('path/to/serviceAccountKey.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://your-database-name.firebaseio.com'
})

ref = db.reference('path/to/store_data')  # Replace with your desired storage path

# Simulating multiple data uploads with a delay
for i in range(5):  # Change the number of iterations as needed
    data_to_upload = {
        f'sensor_reading_{i}': 25.5 + i,  # Example: Creating keys like 'sensor_reading_0', 'sensor_reading_1', ...
        f'delay_{i}': f"{i} seconds delay"  # Example: Creating keys like 'delay_0', 'delay_1', ...
    }

    ref.push(data_to_upload)
    
    # Introduce a delay between uploads
    time.sleep(5)  # Change the delay duration (in seconds) as needed
