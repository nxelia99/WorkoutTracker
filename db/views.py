from datetime import timedelta
import datetime
import traceback
from typing import Collection, Set
from bson import ObjectId
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import jwt
import secrets
from passlib.context import CryptContext
from db import database
from fastapi import Depends
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta



# Configuración de hashing de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], default="bcrypt")
templates = Jinja2Templates(directory="templates")

# Token de autenticación
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Configuración de JWT
SECRET_KEY = secrets.token_bytes(16)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120


# Funciones de autenticación y autorización
async def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

async def verify_token(request: Request):
    token_cookie = request.cookies.get("Authorization")
    if not token_cookie:
        raise HTTPException(status_code=401, detail="No se encontró el token en la cookie")
    

async def create_access_token(username: str):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": username, "exp": expire.timestamp()}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt



async def register(request: Request):
    form_data = await request.form()
    username = form_data["username"]
    password = form_data["password"]
    email = form_data["email"]
    hashed_password = pwd_context.hash(password)
    user = {"username": username, "password": hashed_password, "email": email}
    database.users_collection.insert_one(user)
    return templates.TemplateResponse("register.html", {"request": request, "username":username, "password":password, "email":email})

async def get_register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

async def login_form():
    return open("login.html", "r").read()

async def login(request: Request):
    form_data = await request.form()
    username = form_data["username"]
    password = form_data["password"]
    user = database.users_collection.find_one({"username": username})
    if not user or not await verify_password(password, user["password"]):
        raise HTTPException(status_code=401, detail="Contraseña o usuario incorrecto")
    # Acceder al ID del usuario
    token = await create_access_token(username)  # Pasar username a create_access_token
    return {"access_token": token, "token_type": "bearer"}


async def index_historial(request: Request):
    sessions = list(database.sessions.find())
    
    return templates.TemplateResponse("index.html", {"request": request, "sessions": sessions})

async def get_sesion(sesion_id: str):
    try:
        # Busca la sesión en la base de datos usando el ObjectId
        sesion = database.sessions.find_one({"_id": ObjectId(sesion_id)})
        if sesion:
            # Extrae el nombre, los músculos y los ejercicios
            workout_name = sesion.get("nombre", "")
            musculos = sesion.get("musculos", "")
            exercises = sesion.get("exercises", [])
            
            # Verifica que exercises es una lista y estructura los datos correctamente
            if isinstance(exercises, list):
                exercise_list = []
                for exercise in exercises:
                    if isinstance(exercise, dict):
                        exercise_info = {
                            "name": exercise.get("name", ""),
                            "sets": [{"set": s.get("set", ""), "kg": s.get("kg", "")} for s in exercise.get("sets", [])]
                        }
                        exercise_list.append(exercise_info)
                    else:
                        exercise_list.append({"name": exercise, "sets": []})
            else:
                exercise_list = []

            # Devuelve los datos estructurados como JSON
            return JSONResponse(content={"nombre": workout_name, "musculos": musculos, "exercises": exercise_list})
        
        # Devolver un error 404 si no se encuentra la sesión
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    except Exception as e:
        # Toma y muestra el error en el servidor
        print("Error al procesar la solicitud:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Error interno del servidor")
async def crearworkout_post(request: Request):
    form_data = await request.form()
    nombre = form_data.get("nombre")
    musculos = form_data.get("musculos")
    ejercicios = form_data.getlist("exercise_names")
    # Guardar los datos en la bd
    workout_data = {
        "name": nombre,
        "muscles": musculos,
        "exercises": ejercicios
    }
        # Guardar el diccionario en la base de datos
    result = database.workout_collection.insert_one(workout_data)
   # Preparar la respuesta
    return templates.TemplateResponse("entrenamientocreado.html", {"request": request, "result": result})


async def get_workouts(request: Request):
    workouts = list(database.workout_collection.find())
    return templates.TemplateResponse("añadirentrenamiento2.html", {"request": request, "workouts": workouts})

async def get_exercises(workout_id: str):
    workout = database.workout_collection.find_one({"_id": ObjectId(workout_id)})
    if workout:
        exercises = workout.get("exercises", [])
        # Si el entrenamiento se encuentra, obtener el nombre
        workout_name = workout.get("name", "")
        if isinstance(exercises, list):
            # Asegúrate de que la lista contiene sólo nombres de ejercicios
            return [exercise['name'] if isinstance(exercise, dict) else exercise for exercise in exercises], workout_name
        else:
            try:
                exercise_list = eval(exercises)
                return [exercise['name'] if isinstance(exercise, dict) else exercise for exercise in exercise_list]
            except Exception as e:
                print("Error al convertir la cadena de ejercicios en lista:", e)
                return []
    return []

async def añadirsession(request: Request):
    form_data = await request.form()
    workout_id = form_data.get("workout-select")
    fecha = form_data.get("fecha")
    # Obtener los nombres de los ejercicios del formulario
    exercises = []

    exercise_indices = [key.split("-")[1] for key in form_data.keys() if key.startswith("sets-")]

    exercises1 = [form_data.get(f"exercise-name-{index}") for index in exercise_indices]
    print (exercises1)

    #iterar los nombres de ejericios, sets y kgs por set
    for index, exercise_name in enumerate(exercises1, start=1):
        sets_count = int(form_data[f"sets-{index}"])
        kg_values = form_data[f"kgs-{index}"].split(",")
        kg_values = [float(kg.strip()) for kg in kg_values]

        #si no coinciden el numero de valores de kg con el de sets, mostramos el error
        if len(kg_values) != sets_count:
            raise HTTPException(status_code=400, detail=f"El número de sets y los pesos no coinciden para el ejercicio en la posición: {index}")

        sets_data = [{"set": i + 1, "kg": kg_values[i]} for i in range(sets_count)]
        exercises.append({"name": exercise_name, "sets": sets_data})

    workout = database.workout_collection.find_one({"_id": ObjectId(workout_id)})
    if workout:
        nombre = workout.get("name", "")
        musculos = workout.get("muscles", "")
    workout_data = {
        "workout_id": workout_id,
        "exercises": exercises,
        "fecha": fecha,
        "nombre": nombre,
        "musculos": musculos
    }

    await save_workout_to_db(workout_data)

    return templates.TemplateResponse("entrenamientoañadido.html", {"request": request})


async def save_workout_to_db(workout_data: dict):
    try:
        database.sessions.insert_one(workout_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))