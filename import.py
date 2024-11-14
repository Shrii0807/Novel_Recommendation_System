from pymongo import MongoClient

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['novel_db']
collection = db['novels']

# Fetch one document
sample_document = collection.find_one()
print(sample_document)
