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
        'sensor_reading': 25.5 + i,  # Replace this with your sensor reading or any data
        'delay': f"{i} seconds delay"  # Adding a delay indicator in the data
    }

    ref.push(data_to_upload)
    
    # Introduce a delay between uploads
    time.sleep(5)  # Change the delay duration (in seconds) as needed
