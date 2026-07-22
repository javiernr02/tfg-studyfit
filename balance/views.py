from django.shortcuts import render
from django.utils import timezone
from django.utils.formats import date_format
import core.models as models
from datetime import date, timedelta, datetime
from core.views import format_duration
from django.db.models import Sum, Avg
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from django.http import JsonResponse
import numpy as np
import pandas as pd
from .services.ai_service import get_hybrid_prediction, get_scatter_data_grouped, get_regression_curve, get_regression_curve_global
from sklearn.linear_model import LinearRegression
import math

# Create your views here.


# Gamificación equilibrio mente-cuerpo


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

# Racha en días que se consigue trofeos acumulables definidos (id=7, id=8)
# Se empieza por día actual y se va calculando para días anteriores
# Si un día no se han conseguido ambos trofeos se cancela la racha acumulada
def streak(user):
    
    today = timezone.now().date()
    streak = 0
    i = 0
    
    user_trophies = models.UserTrophy.objects.filter(user=user).select_related('trophy')
    
    while i < 10:
        
        repeatable_student_trophy_obtained_today = user_trophies.filter(obtained_at__date=today, trophy_id=7).exists()
        repeatable_sportsman_trophy_obtained_today = user_trophies.filter(obtained_at__date=today, trophy_id=8).exists()
        
        if repeatable_student_trophy_obtained_today and repeatable_sportsman_trophy_obtained_today:
            streak += 1
            today -= timedelta(days=1)
            i += 1
        else:
            break
        
    return streak

# Cálculo de las horas de estudio y deporte para el día actual, de si se cumple balance entre
# días de estudio y deporte, racha de balance, racha de logros acumulables, y nivel y puntos de experiencia del usuario.
# Todos estos datos se guardan para pasarse como contexto en la función principal: balance
def get_balance_data(user):
    
    today = timezone.now().date()
    
    today_activities = user.activities.filter(date__date=today)
    
    study_durations = timedelta()
    sport_durations = timedelta()
    
    today_study_activities = []
    today_sport_activities = []
    
    balance_value = False
    
    balance_streak_value = 0
    
    streak_value = 0
    
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
        
        streak_value = streak(user)
        
    study_durations_format = format_duration(study_durations)
    sport_durations_format = format_duration(sport_durations)
        
    return {
        'today_study_activities': today_study_activities,
        'today_sport_activities': today_sport_activities,
        'study_durations_format': study_durations_format,
        'sport_durations_format': sport_durations_format,
        'balance_value': balance_value,
        'balance_streak_value': balance_streak_value,
        'streak_value': streak_value
    }

# Obtención de diferentes datos relacionados con los trofeos repetibles (acumulables) y no repetibles (exclusivos)
# Todos estos datos se guardan para pasarse como contexto en la función principal: balance
def get_trophies_data(user):
    user_trophies = models.UserTrophy.objects.filter(user=user).select_related('trophy')
    
    repeatable_student_trophy = models.Trophy.objects.get(id=7)
    repeatable_sportsman_trophy = models.Trophy.objects.get(id=8)
    
    repeatable_trophies_count = user.trophies.filter(is_repeatable=True).count()
    non_repeatable_trophies = user_trophies.filter(trophy__is_repeatable=False)
    non_repeatable_trophies_count = user.trophies.filter(is_repeatable=False).count()
    
    non_obtained_non_repeatable_trophies = models.Trophy.objects.filter(is_repeatable=False).exclude(usertrophy__user=user)
    
    repeatable_student_trophy_obtained_today = user_trophies.filter(obtained_at__date=date.today(), trophy_id=7).exists()
    repeatable_sportsman_trophy_obtained_today = user_trophies.filter(obtained_at__date=date.today(), trophy_id=8).exists()
    
    return {
        'repeatable_trophies_count': repeatable_trophies_count,
        'non_repeatable_trophies': non_repeatable_trophies,
        'non_repeatable_trophies_count': non_repeatable_trophies_count,
        'non_obtained_non_repeatable_trophies': non_obtained_non_repeatable_trophies,
        'repeatable_student_trophy_obtained_today': repeatable_student_trophy_obtained_today,
        'repeatable_sportsman_trophy_obtained_today': repeatable_sportsman_trophy_obtained_today,
        'repeatable_student_trophy': repeatable_student_trophy,
        'repeatable_sportsman_trophy': repeatable_sportsman_trophy
    }
    
# Estadísticas equilibrio mente-cuerpo


# Función para cálculo de la productividad.
# Existe productividad cuando mínimo se estudia 1 hora y se hace media hora de deporte
def get_most_productive(study_activities, sport_activities, trunc, format):
    MIN_STUDY_TIME = timedelta(minutes=60)
    MIN_SPORT_TIME = timedelta(minutes=30)
    
    study = (study_activities.annotate(period=trunc('date')).values('period').annotate(total_duration=Sum('duration')))
    
    sport = (sport_activities.annotate(period=trunc('date')).values('period').annotate(total_duration=Sum('duration')))
    
    study_dict = {i['period']: i['total_duration'] or timedelta(0) for i in study}
    
    sport_dict = {i['period']: i['total_duration'] or timedelta(0) for i in sport}
    
    periods = set(study_dict.keys()).union(set(sport_dict.keys()))
    
    best_period = None
    best_total = timedelta(0)
    
    for period in periods:
        study_time = study_dict.get(period, timedelta(0))
        sport_time = sport_dict.get(period, timedelta(0))
        
        if study_time >= MIN_STUDY_TIME and sport_time >= MIN_SPORT_TIME:
            total_time = study_time + sport_time
            
            if total_time > best_total:
                best_total = total_time
                
                if trunc == TruncDate:
                    date = period.strftime('%d/%m/%Y')
                    
                elif trunc == TruncWeek:
                    date = f"Semana del {period.strftime('%d/%m/%Y')}"
                    
                elif trunc == TruncMonth:
                    date = date_format(period, "F Y").capitalize()
                
                best_period = {
                    'date': date, 
                    'study_time': format(study_time),
                    'sport_time': format(sport_time),
                    'total_time': format(total_time)
                }
                
    return best_period

# Cálculo de los valores para dibujar gráficas en Chart.js, de medias de horas de estudio y deporte, además de
# medias para días activos y de cálculo de la productividad.
# Los cálculos a realizar dependen del filtro por periodo seleccionado: semana, mes, año y global
def stats(request):
    user = models.CustomUser.objects.first()
    
    period = request.GET.get('period', 'week')
    
    study_activities = models.StudyActivity.objects.filter(user=user)
    sport_activities = models.SportActivity.objects.filter(user=user)
    
    # Filtros por periodo
    today = timezone.now().date()
    
    start_week = timezone.make_aware(datetime.combine(today - timedelta(days=7), datetime.min.time()))
    start_month = timezone.make_aware(datetime.combine(today - timedelta(days=30), datetime.min.time()))
    start_year = timezone.make_aware(datetime.combine(today - timedelta(days=365), datetime.min.time()))
    
    if period == 'week':
        study_activities = study_activities.filter(date__gte=start_week)
        sport_activities = sport_activities.filter(date__gte=start_week)
        
    elif period == 'month':
        study_activities = study_activities.filter(date__gte=start_month)
        sport_activities = sport_activities.filter(date__gte=start_month)
        
    elif period == 'year':
        study_activities = study_activities.filter(date__gte=start_year)
        sport_activities = sport_activities.filter(date__gte=start_year)
    
    elif period == 'global':
        study_activities = study_activities
        sport_activities = sport_activities
        
    study_data = (study_activities.annotate(day=TruncDate('date')).values('day').annotate(total_duration=Sum('duration')).order_by('day'))
    sport_data = (sport_activities.annotate(day=TruncDate('date')).values('day').annotate(total_duration=Sum('duration')).order_by('day'))
    
    study_dict = {i['day']: i['total_duration'] or timedelta(0) for i in study_data}
    sport_dict = {i['day']: i['total_duration'] or timedelta(0) for i in sport_data}
    
    all_days = sorted(set(study_dict.keys()).union(set(sport_dict.keys())))
    
    labels = [i.strftime('%d/%m/%Y') for i in all_days]
    
    study_values = [study_dict.get(i, timedelta(0)).total_seconds() for i in all_days]
    
    sport_values = [sport_dict.get(i, timedelta(0)).total_seconds() for i in all_days]
    
    study_labels_formatted = [format_duration(study_dict.get(i, timedelta(0))) for i in all_days]
    
    sport_labels_formatted = [format_duration(sport_dict.get(i, timedelta(0))) for i in all_days]
    
    study_total_time = sum(study_dict.values(), timedelta(0))
    sport_total_time = sum(sport_dict.values(), timedelta(0))
    
    # Cálculo de porcentajes para mostrar en gráfico
    study_total_seconds = study_total_time.total_seconds()
    sport_total_seconds = sport_total_time.total_seconds()
    
    total = study_total_seconds + sport_total_seconds
    
    if total > 0:
        study_percent = (study_total_seconds / total) * 100
        sport_percent = (sport_total_seconds / total) * 100
    else:
        study_percent = 0
        sport_percent = 0
    
    study_total_time_formatted = format_duration(study_total_time)
    sport_total_time_formatted = format_duration(sport_total_time)
    
    # Cálculo de medias
    first_study_activity = study_activities.order_by('date').first()
    
    study_active_days = len(study_data)
    
    if period in ['week', 'month', 'year']:
        total_study_days = len(all_days)
    else:
        if first_study_activity:
            total_study_days = (today - first_study_activity.date.date()).days + 1
        else:
            total_study_days = 1
    
    if study_total_seconds > 0:
        study_average_hours = (study_total_seconds / 3600) / total_study_days
        study_average = timedelta(hours=study_average_hours)
    else:
        study_average = timedelta(0)
        
    if study_active_days > 0:
        study_active_average_hours = (study_total_seconds / 3600) / study_active_days
        study_active_average = timedelta(hours=study_active_average_hours)
    else:
        study_active_average = timedelta(0)
    
    
    first_sport_activity = sport_activities.order_by('date').first()
    
    sport_active_days = len(sport_data)
    
    if period in ['week', 'month', 'year']:
        total_sport_days = len(all_days)
    else:
        if first_sport_activity:
            total_sport_days = (today - first_sport_activity.date.date()).days + 1
        else:
            total_sport_days = 1
            
    if sport_total_seconds > 0:
        sport_average_hours = (sport_total_seconds / 3600) / total_sport_days
        sport_average = timedelta(hours=sport_average_hours)
    else:
        sport_average = timedelta(0)
    
    if sport_active_days > 0:
        sport_active_average_hours = (sport_total_seconds / 3600) / sport_active_days
        sport_active_average = timedelta(hours=sport_active_average_hours)
    else:
        sport_active_average = timedelta(0)

    
    # Cálculo de productividad
    productive_stats = {
        'best_day': get_most_productive(
            study_activities,
            sport_activities,
            TruncDate,
            format_duration
        )
    }
    
    if period in ['month', 'year', 'global']:
        productive_stats['best_week'] = get_most_productive(
            study_activities,
            sport_activities,
            TruncWeek,
            format_duration
        )
        
    if period in ['year', 'global']:
        productive_stats['best_month'] = get_most_productive(
            study_activities,
            sport_activities,
            TruncMonth,
            format_duration
        )
    
    return JsonResponse({
        'labels': labels,
        'study_values': study_values,
        'sport_values': sport_values,
        'study_labels_formatted': study_labels_formatted,
        'sport_labels_formatted': sport_labels_formatted,
        'study_total_time': study_total_seconds,
        'sport_total_time': sport_total_seconds,
        'study_total_time_formatted': study_total_time_formatted,
        'sport_total_time_formatted': sport_total_time_formatted,
        'study_percent': round(study_percent, 1),
        'sport_percent': round(sport_percent, 1),
        'study_average': format_duration(study_average),
        'study_active_average': format_duration(study_active_average),
        'sport_average': format_duration(sport_average),
        'sport_active_average': format_duration(sport_active_average),
        'productive_stats': productive_stats
    })
    
# Análisis inteligente equilibrio mente-cuerpo

# Obtención para el usuario correspondiente de los puntos para la gráfica de dispersión,
# curva de regresión personal con zona recomendada de deporte y valor óptimo de horas-concentración, y
# curva de regresión global de la aplicación  
def scatter_view(request):
    user = models.CustomUser.objects.get(id=4)
    
    regression = get_regression_curve(user)
    regression_global = get_regression_curve_global()

    return JsonResponse({
        "points": get_scatter_data_grouped(user),
        "curve": regression["curve"],
        "best": regression["best"],
        "zone": regression["zone"],
        "curve_global": regression_global["curve_global"]
    })
         
# Función principal balance que renderiza la página html con todos los datos calculados en las funciones anteriores,
# además de lo relacionado con niveles, puntos de experiencia, valor de predicción de la concentración
# y progreso dinámico del deporte realizado en el día actual
def balance(request):
    user = models.CustomUser.objects.get(id=4)
    
    today = timezone.now().date()
    sport_durations = timedelta()
    
    level = user.level
    experience_points = user.experience_points
    
    remaining_points = 1000 - experience_points
    
    hybrid_prediction = get_hybrid_prediction(user)
    
    today_sport_activities = models.SportActivity.objects.filter(user=user, date__date=today)
    
    for i in today_sport_activities:
        sport_durations += i.duration
    
    today_sport_hours = sport_durations.total_seconds() / 3600
    
    today_sport_hours_format = format_duration(timedelta(hours=today_sport_hours))
    
    regression = get_regression_curve(user)
    regression_global = get_regression_curve_global()
        
    if regression["best"]:
        
        best_sport_hours = regression["best"]["x"]
        
        remaining_sport_hours = max(0, best_sport_hours - today_sport_hours)
        
        remaining_sport_hours = format_duration(timedelta(hours=remaining_sport_hours))
        
        recommended_zone = regression["zone"]
        
    else:
        remaining_sport_hours = None
        
        recommended_zone = None
        
    if recommended_zone:
        max_hours = math.ceil(regression["max_sport_hours"])

        progress = (today_sport_hours / max_hours) * 100
        progress = max(0, min(progress, 100))

        zone_start = (recommended_zone["min_x"] / max_hours) * 100
        zone_width = ((recommended_zone["max_x"] - recommended_zone["min_x"]) / max_hours) * 100
        zone_end = zone_start + zone_width
        
        max_hours_format = format_duration(timedelta(hours=max_hours))
        
        max_zone_hours_format = format_duration(timedelta(hours=recommended_zone["max_x"]))
        
        min_zone_hours_format = format_duration(timedelta(hours=recommended_zone["min_x"]))
        
    else:
        progress = None
        zone_start = None
        zone_width = None
    
    return render(request, 'balance.html', {
        'user': user,
        'level': level,
        'experience_points': experience_points,
        'remaining_points': remaining_points,
        'today_sport_hours_format': today_sport_hours_format,
        'recommended_zone': recommended_zone,
        'max_hours_format': max_hours_format,
        'max_zone_hours_format': max_zone_hours_format,
        'min_zone_hours_format': min_zone_hours_format,
        'progress': progress,
        'zone_start': zone_start,
        'zone_width': zone_width,
        'zone_end': zone_end,
        'remaining_sport_hours': remaining_sport_hours,
        'global_regression_date': regression_global['generated_at'],
        
        **get_balance_data(user),
        **get_trophies_data(user),
        
        "prediction": hybrid_prediction.get("prediction"),
        "global": hybrid_prediction.get("global"),
        "personal": hybrid_prediction.get("personal"),
        "mode": hybrid_prediction.get("mode")
    })
    
    