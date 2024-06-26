from pymongo import MongoClient

# Configuración de la base de datos
client = MongoClient("mongodb+srv://admin:X3dYaZzAIwEeinqq@cluster.cf1dvmy.mongodb.net/?retryWrites=true&w=majority")
db = client["cegym"]
users_collection = db["users"]
workout_collection = db["workouts"]
sessions = db["sessions"]

