import firebase_admin
from firebase_admin import credentials, db
import time

# Initialize Firebase
cred = credentials.Certificate('path/to/serviceAccountKey.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://your-database-name.firebaseio.com'
})

ref = db.reference('path/to/store_data')  # Replace with your desired storage path

data_to_upload = {
    'sensor_reading': 25.5,  # Replace this with your sensor reading
    'timestamp': '2024-01-10 12:00:00'  # Replace with your timestamp or any other relevant data
}

ref.push(data_to_upload)
