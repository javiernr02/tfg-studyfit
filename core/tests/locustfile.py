from locust import HttpUser, task, between
import json
from pathlib import Path

# Carga de usuarios del archivo seed.py
BASE_DIR = Path(__file__).resolve().parents[2]

with open(BASE_DIR / "populate" / "locust_users.json",
    encoding="utf-8"
) as file:
    USERS = json.load(file)
    
next_user_index = 0


class StudyFitUser(HttpUser):
    
    wait_time = between(1, 3)
    
    def on_start(self):
        global next_user_index
        
        print(f"Usuarios disponibles: {len(USERS)}")
        print(f"Índice asignado: {next_user_index}")
        
        if next_user_index >= len(USERS):
            raise RuntimeError("No hay suficientes datos")
        
        # Asignación de usuarios
        self.username = USERS[next_user_index]
        next_user_index += 1
        
        self.password = "Studyfit1!"
        
        response = self.client.get("/")
        
        csrf_token = self.client.cookies.get("csrftoken")
        
        response = self.client.post(
            "/login/",
            data={
                "username": self.username,
                "password": self.password,
            },
            name="login",
            headers={
                "X-CSRFToken": csrf_token
            }
        )
        
        if response.status_code not in (200, 302):
            response.failure(f"El usuario {self.username} no pudo iniciar sesión")
            
    @task(5)
    def home(self):
        self.client.get("/home/", name="home")
        
    @task(4)
    def activity_history(self):
        self.client.get("/activity-history/", name="activity_history")
        
    @task(3)
    def balance(self):
        self.client.get("/balance/", name="balance")
    
    @task(2)
    def stats(self):
        self.client.get("/stats", name="stats")
    
    @task(2)
    def scatter(self):
        self.client.get("/scatter", name="scatter")
        
    