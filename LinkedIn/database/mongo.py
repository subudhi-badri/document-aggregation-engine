import os
import json
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from commander import MONGODB_PASSWORD, MONGODB_USERNAME

uri = f"mongodb+srv://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@cluster0.e20ud.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri, server_api=ServerApi('1'))

try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

def upload_profiles_to_mongodb():
    db = client['Users']  # Replace with your database name
    collection = db['Users']  # Replace with your collection name
    json_directory = 'services/outputs/profile_json/'

    for filename in os.listdir(json_directory):
        if filename.endswith('.json'):
            with open(os.path.join(json_directory, filename), 'r', encoding='utf-8') as file:
                data = json.load(file)
                collection.insert_one(data)
                print(f"Uploaded {filename} to MongoDB.")

# Call the function to upload profiles
upload_profiles_to_mongodb()
