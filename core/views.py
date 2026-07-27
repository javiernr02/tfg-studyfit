from django.shortcuts import render
import core.models as models
from django.utils import timezone
from datetime import timedelta
from collections import defaultdict

# Create your views here.

# Función de formateo de objeto 'duration' según su valor en cadena de texto personalizada
def format_duration(duration):
    
    if duration is None:
        return None
    
    total_seconds = int(duration.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    
    if hours < 1:
        return f'{minutes}min'
    elif minutes == 0:
        return f'{hours}h'
    else:
        return f'{hours}h {minutes}min'
    
# Cálculo en minutos de la lógica de balance de horas de estudio y deporte 
def balance_logic(study_total_minutes, sport_total_minutes):
    
    balance = False
    
    if sport_total_minutes > 0 and study_total_minutes / sport_total_minutes >= 2:
            balance = True
            
    return balance

# Racha en días que se cumple balance de horas de estudio y deporte
# Se empieza por día actual y se va calculando para días anteriores
# Si un día no existe balance se cancela la racha acumulada
def balance_logic_streak(user):
    
    today = timezone.now().date()
    balance_streak = 0
    
    while True:
        
        study_durations = timedelta()
        sport_durations = timedelta()
        
        today_study_activities = models.StudyActivity.objects.filter(user=user,date__date=today)
        
        today_sport_activities = models.SportActivity.objects.filter(user=user,date__date=today)
        
        for i in today_study_activities:
            study_durations += i.duration
            
        for i in today_sport_activities:
            sport_durations += i.duration
            
        study_total_seconds = int(study_durations.total_seconds())
        study_total_minutes = study_total_seconds / 60
        
        sport_total_seconds = int(sport_durations.total_seconds())
        sport_total_minutes = sport_total_seconds / 60
        
        if not today_study_activities and not today_sport_activities:
            break
        
        balance_value = balance_logic(study_total_minutes, sport_total_minutes)
        
        if balance_value:
            balance_streak += 1
            today -= timedelta(days=1)
        else:
            break
        
    return balance_streak

# Cálculo de las horas de estudio y deporte para el día actual, de si se cumple balance entre
# días de estudio y deporte, racha de balance. Todos estos datos se guardan para pasarse como 
# contexto en la función principal: home
def get_balance_data(user):
    
    today = timezone.now().date()
    
    today_activities = user.activities.filter(date__date=today)
    
    study_durations = timedelta()
    sport_durations = timedelta()
    
    today_study_activities = []
    today_sport_activities = []
    
    balance_value = False
    
    balance_streak_value = 0
    
    if today_activities:
        today_study_activities = models.StudyActivity.objects.filter(user=user,date__date=today)
        
        today_sport_activities = models.SportActivity.objects.filter(user=user,date__date=today)
        
        for i in today_study_activities:
            study_durations += i.duration
            
        for i in today_sport_activities:
            sport_durations += i.duration
            
        study_total_seconds = int(study_durations.total_seconds())
        study_total_minutes = study_total_seconds / 60
        
        sport_total_seconds = int(sport_durations.total_seconds())
        sport_total_minutes = sport_total_seconds / 60
        
        balance_value = balance_logic(study_total_minutes, sport_total_minutes)
        
        balance_streak_value = balance_logic_streak(user)
                
    study_durations_format = format_duration(study_durations)
    sport_durations_format = format_duration(sport_durations)
        
    return {
        'today_study_activities': today_study_activities,
        'today_sport_activities': today_sport_activities,
        'study_durations_format': study_durations_format,
        'sport_durations_format': sport_durations_format,
        'balance_value': balance_value,
        'balance_streak_value': balance_streak_value
    }

# Renderización de la página principal de la aplicación con información sobre horas de deporte y estudio hoy y totales, cumplimiento
# del equilibrio entre estudio y deporte, número de actividades en los últimos 7 días, y desglose de actividad según su tipo con 
# información sobre sus horas totales y número de actividades
def home(request):
    user = models.CustomUser.objects.first()
    
    activities = user.activities.all()
    
    study_durations = timedelta()
    sport_durations = timedelta()
    
    if activities:
        study_activities = models.StudyActivity.objects.filter(user=user)
        study_activities_by_subjects = defaultdict(lambda: {"duration": timedelta(), "count": 0})
        
        sport_activities = models.SportActivity.objects.filter(user=user)
        sport_activities_by_sport_types = defaultdict(lambda: {"duration": timedelta(), "count": 0})
        
        for i in study_activities:
            subject = i.subject
            study_durations += i.duration
            study_activities_by_subjects[subject]["duration"] += i.duration
            study_activities_by_subjects[subject]["count"] += 1
            
        for i in sport_activities:
            sport_type = i.get_sport_type_display()
            sport_durations += i.duration
            sport_activities_by_sport_types[sport_type]["duration"] += i.duration
            sport_activities_by_sport_types[sport_type]["count"] += 1
            
        study_durations_format = format_duration(study_durations)
        sport_durations_format = format_duration(sport_durations)
        
        study_activities_by_subjects_format = {}
        sport_activities_by_sport_types_format = {}
        
        for subject, i in study_activities_by_subjects.items():
            study_activities_by_subjects_format[subject] = {
                "duration": format_duration(i["duration"]),
                "count": i["count"]
            }
            
        for sport_type, i in sport_activities_by_sport_types.items():
            sport_activities_by_sport_types_format[sport_type] = {
                "duration": format_duration(i["duration"]),
                "count": i["count"]
            }
            
        last_7_days = timezone.now() - timedelta(days=7)
        last_activities = activities.filter(date__gte=last_7_days).count()
    return render(request, 'home.html', 
                  {'user': user,
                    'activities': activities, 
                   'study_durations_format': study_durations_format, 
                   'sport_durations_format': sport_durations_format, 
                   'last_activities': last_activities,
                   'study_activities_by_subjects_format': study_activities_by_subjects_format,
                   'sport_activities_by_sport_types_format': sport_activities_by_sport_types_format,
                   
                   **get_balance_data(user)
                   })