import core.models as models
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestRegressor
from django.conf import settings
from django.db.models import Avg
import os
from core.views import format_duration
from collections import defaultdict
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from datetime import timedelta
from django.core.cache import cache
from django.utils import timezone

MODEL_PATH = os.path.join(settings.BASE_DIR, "ai_models", "global_model.pkl")

INTENSITY = {
    "very_low": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "very_high": 4
}

# Construcción de la tabla (DataFrame en Pandas) donde las filas son las actividades de estudio registradas en la aplicación
# y las columnas: horas de actividad deportiva previa, su intensidad, duración estudio, día de la semana, hora de inicio estudio y concentración
def build_dataset():

    rows = []

    study_activities = models.StudyActivity.objects.select_related('user').all()

    for s in study_activities:

        sport_before = models.SportActivity.objects.filter(user=s.user, date__lt=s.date).order_by("-date").first()

        sport_hours = 0
        intensity = 2

        if sport_before:
            sport_hours = sport_before.duration.total_seconds() / 3600

            intensity = INTENSITY.get(sport_before.intensity, 2)

        rows.append({
            "sport_hours": sport_hours,
            "intensity": intensity,
            "study_duration": s.duration.total_seconds() / 3600,
            "weekday": s.date.weekday(),
            "hour": s.date.hour,
            "concentration": s.concentration
        })

    return pd.DataFrame(rows)

# Entrena el modelo con los datos del dataset anterior y lo guarda en un archivo, siendo la variable objetivo: concentración.
# Utiliza modelo de ia Random Forest para regresión
def train_model():
    
    n = models.StudyActivity.objects.count()
    
    if n < 100:
        raise ValueError("No hay suficientes datos para entrenar el modelo")
    
    df = build_dataset()

    X = df.drop("concentration", axis=1)
    y = df["concentration"]

    model = RandomForestRegressor(n_estimators=200, max_depth=12, random_state=26)

    model.fit(X, y)

    joblib.dump(model, MODEL_PATH)

# Carga el modelo entrenado, si existe
def load_model():
    
    if os.path.exists(MODEL_PATH):
        
        return joblib.load(MODEL_PATH)
    
    return None

# Genera predicción de la concentración utilizando el modelo global entrenado y hábitos medios del usuario
# (última actividad de deporte, duración media de estudio, día de la semana y hora de inicio de estudio)
def get_global_prediction(user):
    
    global_model = load_model()
    
    study_activities = models.StudyActivity.objects.filter(user=user)
    
    if global_model is None:
        return None

    if not study_activities.exists():
        return None
    
    avg = study_activities.aggregate(avg=Avg("duration"))["avg"]
    
    if avg:
        avg_duration =  avg.total_seconds() / 3600
    else:
        avg_duration = 0

    avg_hour = sum([s.date.hour for s in study_activities]) / study_activities.count()

    avg_weekday = sum([s.date.weekday() for s in study_activities]) / study_activities.count()

    sport_before = models.SportActivity.objects.filter(user=user).order_by("-date").first()

    sport_hours = 0
    intensity = 2

    if sport_before:
        sport_hours = sport_before.duration.total_seconds() / 3600

        intensity = INTENSITY.get(sport_before.intensity, 2)

    x = pd.DataFrame([{
        "sport_hours": sport_hours,
        "intensity": intensity,
        "study_duration": avg_duration,
        "weekday": avg_weekday,
        "hour": avg_hour
    }])

    return float(global_model.predict(x)[0])

# Cálculo de pesos para modelo global y modelo personal del usuario, que aumenta conforme registra más actividades, pero
# siempre hay un impacto mínimo del modelo global
def get_hybrid_weights(user):

    n = models.StudyActivity.objects.filter(user=user).count()

    MIN = 10
    FULL = 70
    MIN_GLOBAL = 0.2
    
    if n <= MIN:
        personal_weight = 0.0

    else:
        personal_weight = (n - MIN) / (FULL - MIN)
        personal_weight = max(0.0, min(1.0, personal_weight))
        
    global_weight = max(MIN_GLOBAL, 1 - personal_weight)
    
    total = personal_weight + global_weight
    
    personal_weight /= total
    global_weight /= total

    return personal_weight, global_weight

# Proporcina predicción híbrida de la concentración basada en el modelo global y los datos de concentración históricos
# del usuario
def get_hybrid_prediction(user):

    global_prediction = get_global_prediction(user)

    study_activities = models.StudyActivity.objects.filter(user=user)

    personal_prediction = study_activities.aggregate(avg=Avg("concentration"))["avg"]
    
    if global_prediction is None:
        return {
            "prediction": None,
            "mode": "insufficient_data"
        }

    if personal_prediction is None:
        return {
            "prediction": int(round(global_prediction)),
            "mode": "global"
        }

    personal_weight, global_weight = get_hybrid_weights(user)

    hybrid_prediction = (personal_prediction * personal_weight) + (global_prediction * global_weight)

    return {
        "prediction": int(round(hybrid_prediction)),
        "global": int(round(global_prediction)),
        "personal": int(round(personal_prediction)),
        "global_weight": round(global_weight, 2),
        "personal_weight": round(personal_weight, 2),
        "mode": "hybrid"
    }

# Obtiene los puntos para la gráfica de dispersión: duración de deporte, concentración
def get_scatter_data(user):
    
    points = []

    study_activities = list(models.StudyActivity.objects.filter(user=user).order_by("date"))
    
    for s in study_activities:
        
        sport_hours = 0
        sport_hours_format_duration = "0min"
        
        sport_before = (models.SportActivity.objects.filter(user=user, date__date=s.date.date(), date__lt=s.date).order_by("-date").first())

        if sport_before:
            sport_hours = sport_before.duration.total_seconds() / 3600
            sport_hours_format_duration = format_duration(sport_before.duration)
                    
        points.append({
            "sport_hours": sport_hours,
            "sport_hours_format_duration": sport_hours_format_duration,
            "concentration": s.concentration,
            "sessions": 1
        })

    return points

# Agrupa los puntos por duración de deporte y concentración para contabilizarlos y mostrarlos de forma agrupada
def get_scatter_data_grouped(user):

    original_points = get_scatter_data(user)

    grouped = defaultdict(lambda: {
        "sessions": 0,
        "sport_hours_format_duration": ""
    })

    for point in original_points:

        key = (
            point["sport_hours"],
            point["concentration"]
        )

        grouped[key]["sessions"] += 1
        grouped[key]["sport_hours_format_duration"] = point["sport_hours_format_duration"]

    return [
        {
            "sport_hours": key[0],
            "concentration": key[1],
            "sessions": value["sessions"],
            "sport_hours_format_duration": value["sport_hours_format_duration"]
        }
        for key, value in grouped.items()
    ]

# Cálculo de la función de regresión polinómica de grado 2 para mostrar la tendencia positiva y negativa entre horas de deporte y concentración.
# Cálculo de mejor punto y zona recomendada
def get_regression_curve(user):
    
    points = get_scatter_data(user)

    if len(points) < 3:
        return {
            "curve": [],
            "best": None,
            "zone": []
        }

    X = np.array([p["sport_hours"] for p in points]).reshape(-1, 1)
    y = np.array([p["concentration"] for p in points])
    
    polynomial = PolynomialFeatures(degree=2)
    X_polynomial = polynomial.fit_transform(X)

    model = LinearRegression()
    model.fit(X_polynomial, y)

    x_curve = np.linspace(X.min(), X.max(), 200).reshape(-1, 1)
    y_curve = model.predict(polynomial.transform(x_curve))
    
    # Mejor punto
    best_concentration_id = np.argmax(y_curve)
    
    best_x = float(x_curve[best_concentration_id])
    best = {
        "x": best_x,
        "y": float(y_curve[best_concentration_id]),
        "sport_hours_format_duration": format_duration(timedelta(hours=best_x))
    }
    
    # Zona recomendada (>= 90%)
    limit = np.max(y_curve) * 0.9
    
    zone_points = [float(x) for x, y in zip(x_curve.flatten(), y_curve) if y >= limit]
    
    zone = {"min_x": min(zone_points),"max_x": max(zone_points)}
            
    # Curva
    curve = [
        {
            "x": float(x),
            "y": float(y),
            "sport_hours_format_duration": format_duration(timedelta(hours=float(x)))
        }
        for x, y in zip(x_curve.flatten(), y_curve)
    ]

    return {
        "curve": curve,
        "best": best,
        "zone": zone,
        "max_sport_hours": float(X.max())
    }

# Cálculo de los puntos (horas de deporte, concentración) de los usuarios de la aplicación
def get_scatter_data_global():

    users = models.CustomUser.objects.all()
    
    points = []

    for user in users:

        study_activities = list(models.StudyActivity.objects.filter(user=user).order_by("date"))

        sport_activities = list(models.SportActivity.objects.filter(user=user).order_by("date"))
        
        for s in study_activities:

            sport_before = None

            for sport in sport_activities:
                if sport.date < s.date:
                    sport_before = sport
                else:
                    break

            sport_hours = 0

            if sport_before:
                sport_hours = sport_before.duration.total_seconds() / 3600
            
            points.append({
                "sport_hours": sport_hours,
                "concentration": s.concentration
            })

    return points

# Cálculo de la función de regresión polinómica de grado 2 que toma los datos de los usuarios de la aplicación para mostrar 
# la tendencia positiva y negativa entre horas de deporte y concentración.
# No será necesario calcularlo si ya se encuentra en caché, con un tiempo de expiración de la versión de 24 horas, obteniendo
# la fecha en la que se ha generado
def get_regression_curve_global():
    
    cached = cache.get("global_regression")
    
    if cached:
        return cached
    
    points_global = get_scatter_data_global()
    
    if len(points_global) < 3:
        return {
            "curve_global": []
        }

    X = np.array([p["sport_hours"] for p in points_global]).reshape(-1, 1)
    y = np.array([p["concentration"] for p in points_global])
    
    polynomial = PolynomialFeatures(degree=2)
    X_polynomial = polynomial.fit_transform(X)

    model = LinearRegression()
    model.fit(X_polynomial, y)

    x_curve = np.linspace(0, X.max(), 200).reshape(-1, 1)
    y_curve = model.predict(polynomial.transform(x_curve))
            
    # Curva
    curve_global = [
        {
            "x": float(x),
            "y": float(y),
            "sport_hours_format_duration": format_duration(timedelta(hours=float(x)))
        }
        for x, y in zip(x_curve.flatten(), y_curve)
    ]
    
    result = {
        "curve_global": curve_global,
        "generated_at": timezone.now()
    }
    
    cache.set(
        "global_regression",
        result,
        timeout=60 * 60 * 24   # 24 horas para que caduque la versión global de la curva de regresión
    )

    return result