from django.shortcuts import render
from django.utils import timezone
import core.models as models
from datetime import date, timedelta
from core.views import format_duration
from django.db.models import Sum
from django.db.models.functions import TruncDate
from django.http import JsonResponse

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
        
        today_study_activities = models.StudyActivity.objects.filter(user=user,date=today)
        
        today_sport_activities = models.SportActivity.objects.filter(user=user,date=today)
        
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
    
    today_activities = user.activities.filter(date=today)
    
    study_durations = timedelta()
    sport_durations = timedelta()
    
    today_study_activities = []
    today_sport_activities = []
    
    balance_value = False
    
    balance_streak_value = 0
    
    streak_value = 0
    
    if today_activities:
        today_study_activities = models.StudyActivity.objects.filter(user=user,date=today)
        
        today_sport_activities = models.SportActivity.objects.filter(user=user,date=today)
        
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
    
# Función principal balance que renderiza la página html con todos los datos calculados en las funciones anteriores,
# además de lo relacionado con niveles y puntos de experiencia
def balance(request):
    user = models.CustomUser.objects.first()
    
    level = user.level
    experience_points = user.experience_points
    
    remaining_points = 1000 - experience_points
    
    return render(request, 'balance.html', {
        'user': user,
        'level': level,
        'experience_points': experience_points,
        'remaining_points': remaining_points,
        **get_balance_data(user),
        **get_trophies_data(user)
    })


# Estadísticas equilibrio mente-cuerpo


def stats(request):
    user = models.CustomUser.objects.first()
    
    period = request.GET.get('period', 'week')
    
    study_activities = models.StudyActivity.objects.filter(user=user)
    sport_activities = models.SportActivity.objects.filter(user=user)
    
    # Filtros para la gráfica
    today = timezone.now().date()
    
    if period == 'week':
        study_activities = study_activities.filter(date__gte=today - timedelta(days=7))
        sport_activities = sport_activities.filter(date__gte=today - timedelta(days=7))
        
    elif period == 'month':
        study_activities = study_activities.filter(date__gte=today - timedelta(days=30))
        sport_activities = sport_activities.filter(date__gte=today - timedelta(days=30))
        
    elif period == 'year':
        study_activities = study_activities.filter(date__gte=today - timedelta(days=365))
        sport_activities = sport_activities.filter(date__gte=today - timedelta(days=365))
        
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
        'sport_percent': round(sport_percent, 1)
    })
    
    