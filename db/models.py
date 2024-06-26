from pydantic import BaseModel
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

from typing import Dict, List, Optional
from pydantic import BaseModel

class User(BaseModel):
    username: str
    password: str

class Exercise(BaseModel):
    id: str
    name: str
    mechanic: str
    equipment: str
    primaryMuscles: List[str]
    instructions: List[str]
    sets: List[Dict[str, float]] = []

class Workout(BaseModel):
    user_id: str
    exercises: List[str] = []
    sets: List[Dict[str, int]] = []
    date: Optional[str]

class SessionDetails(BaseModel):
    workout_id: str
    exercises: list
    fecha: str

class SetData(BaseModel):
    set: int
    kg: float

class ExerciseData(BaseModel):
    name: str
    sets: List[SetData]

class WorkoutData(BaseModel):
    user_id: str
    workout_id: str
    exercises: List[ExerciseData]
