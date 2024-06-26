import json
import math
from bson import ObjectId
from fastapi import FastAPI, Depends, HTTPException, Query, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, Depends
from db import views
from fastapi.staticfiles import StaticFiles
from pymongo.mongo_client import MongoClient
from fastapi import Depends, HTTPException, FastAPI
from fastapi.security import OAuth2PasswordBearer


# Crea la instancia de la aplicación FastAPI
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
uri = "mongodb+srv://admin:X3dYaZzAIwEeinqq@cluster.cf1dvmy.mongodb.net/?retryWrites=true&w=majority"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
# Create a new client and connect to the server
client = MongoClient(uri)

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)



#endpoints para el manejo del registro
@app.post("/register")
async def post_register(request: Request):
    return await views.register(request)
@app.get("/register")
async def get_register(request: Request):
    return await views.get_register(request)

# endpoints para el manejo de inicio de sesión
@app.get("/login")
async def get_login(request: Request):
    return templates.TemplateResponse("login.html", {"request":request})

@app.post("/login")
async def post_login(request: Request):
    response_data = await views.login(request)
    if "access_token" in response_data:
        token = response_data["access_token"]
        response = RedirectResponse(url="/index")
        response.set_cookie(key="Authorization", value=f"{token}", httponly=True)
        return response
    else:
        raise HTTPException(status_code=401, detail="Contraseña o usuario incorrecto")


@app.get("/index")
async def get_index(request: Request, token: str = Depends(views.verify_token)):
    return await views.index_historial(request)

@app.post("/index")
async def post_index(request: Request, token: str = Depends(views.verify_token)):
    return await views.index_historial(request)

@app.get("/crearworkout")
async def crear_workout(request: Request, token: str = Depends(views.verify_token)):
    with open('db/utils/exercises.json', 'r') as f:
        exercises = json.load(f)
    return templates.TemplateResponse("crearworkout.html", {"request": request, 'all_exercises': exercises})

@app.post("/crearworkout")
async def crearworkout(request: Request, token: str = Depends(views.verify_token)):
    return await views.crearworkout_post(request)

@app.get("/api/workout/{workout_id}")
async def get_workout(workout_id: str):
    # Obtener los nombres de los ejercicios correspondientes al workout_id
    exercise_names = await views.get_exercises(workout_id)
    return {"exercises": exercise_names}

@app.get("/workoutexistente")
async def getworkout(request: Request, token: str = Depends(views.verify_token)):
    return await views.get_workouts(request)

@app.post("/savesession")
async def save_session(request: Request):
    return await views.añadirsession(request)

@app.get("/api/workout/sesion/{sesion_id}")
async def detalles_sesion(sesion_id: str):
    return await views.get_sesion(sesion_id)

@app.get("/bibliotecaejercicios")
async def get_biblioteca(request: Request, page: int = Query(1, alias='page', gt=0), token: str = Depends(views.verify_token)):
    with open("db/utils/exercises.json", "r") as file:
        ejercicios = json.load(file)
    
    items_per_page = 10
    total_items = len(ejercicios)
    total_pages = math.ceil(total_items / items_per_page)
    
    start_item = (page - 1) * items_per_page
    end_item = start_item + items_per_page
    ejercicios_paginated = ejercicios[start_item:end_item]
    
    return templates.TemplateResponse("ejercicios.html", {
        "request": request, 
        "ejercicios": ejercicios_paginated, 
        "page": page, 
        "total_pages": total_pages
    })

@app.post("/cerrarsesion")
@app.get("/cerrarsesion")
async def logout(response: Response):
    response = RedirectResponse(url="/login")
    response.delete_cookie(key="Authorization")
    return response