import core.models as models
from django.utils import timezone
from datetime import timedelta
from collections import defaultdict
from .forms import StudyActivityForm, LiveStudyActivityForm, SportActivityForm, LiveSportActivityForm, SubjectForm
from django.shortcuts import render, redirect, get_object_or_404
from datetime import datetime
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import ProtectedError
from django.utils.dateparse import parse_datetime


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
        
    return render(request, 'home.html', {
        'user': user,
        'activities': activities, 
        'study_durations_format': study_durations_format, 
        'sport_durations_format': sport_durations_format, 
        'last_activities': last_activities,
        'study_activities_by_subjects_format': study_activities_by_subjects_format,
        'sport_activities_by_sport_types_format': sport_activities_by_sport_types_format,
        
        **get_balance_data(user)
    })

# Creación de actividad de estudio con gestión de errores en caso de fallar
# o redirigiendo a la página desde donde se hizo la petición en caso de éxito
def create_study_activity(request):
    if request.method == "POST":
        form = StudyActivityForm(request.POST)

        if form.is_valid():
            activity = form.save(commit=False)
            activity.user = models.CustomUser.objects.first()
            
            date = form.cleaned_data["date"]
            start_time = form.cleaned_data["start_time"]
            end_time = form.cleaned_data["end_time"]
            
            start_datetime = timezone.make_aware(datetime.combine(date.date(), start_time))

            end_datetime = timezone.make_aware(datetime.combine(date.date(), end_time))

            activity.date = start_datetime
            activity.duration = end_datetime - start_datetime
            
            activity.save()
            
            messages.success(request, "Actividad de estudio registrada correctamente")
            
            return redirect(request.POST.get("next", "home"))
        
        # Formulario inválido
        request.session["study_form_data"] = request.POST.dict()
        request.session["open_study_modal"] = True
        request.session["open_live_study"] = False
                
        return redirect(request.POST.get("next", "home"))
    
    return redirect("home")

# Creación de asignatura asociada al usuario que la crea o gestión de error en caso de fallar
def create_subject(request):
    if request.method == "POST":
        form = SubjectForm(request.POST)

        if form.is_valid():
            subject = form.save(commit=False)
            subject.user = models.CustomUser.objects.first()
            
            subject.save()

            return JsonResponse({
                "success": True,
                "id": subject.id,
                "name": subject.name,
                "category": subject.get_subject_category_display()
            })

        return JsonResponse({
            "success": False,
            "errors": form.errors.get_json_data()
        }, status=400)

    return JsonResponse({
        "success": False
    }, status=400)

# Eliminación de la asignatura seleccionada asociada al usuario que la elimina o gestión
# de error en caso de fallar, por ejemplo, porque la asignatura tenga actividades de estudio asociadas
def delete_subject(request, subject_id):
    if request.method == "POST":
        subject = get_object_or_404(
            models.Subject,
            id=subject_id,
            user=models.CustomUser.objects.first()
        )
        
        try:
            subject.delete()

            return JsonResponse({
                "success": True
            })

        except ProtectedError:
            return JsonResponse({
                "success": False,
                "error": "No se puede eliminar esta asignatura porque tiene actividades de estudio asociadas"
            })

    return JsonResponse({
        "success": False
    }, status=405)
    
# Creación de actividad de estudio en directo y cálculo de su duración, con gestión de errores en caso de fallar
# o redirigiendo a la página desde donde se hizo la petición en caso de éxito
def create_live_study_activity(request):
    if request.method == "POST":
        form = LiveStudyActivityForm(request.POST)

        if form.is_valid():
            activity = form.save(commit=False)
            activity.user = models.CustomUser.objects.first()

            start_datetime = parse_datetime(request.POST.get("start_datetime"))

            end_datetime = parse_datetime(request.POST.get("end_datetime"))

            paused_duration = timedelta(milliseconds=int(request.POST.get("paused_duration", 0)))

            activity.date = start_datetime
            
            activity.duration = (end_datetime - start_datetime - paused_duration)

            activity.save()
            
            messages.success(request, "Actividad de estudio registrada correctamente")

            return redirect(request.POST.get("next", "home"))
        
        # Formulario inválido
        request.session["live_study_form_data"] = request.POST.dict()
        request.session["open_study_modal"] = True
        request.session["open_live_study"] = True
        request.session["live_study_finished"] = True

        return redirect(request.POST.get("next", "home"))

    return redirect("home")

# Eliminar datos rellenados en la actividad de estudio finalizada
def cancel_study_activity(request):
    request.session.pop("study_form_data", None)
    request.session.pop("open_study_modal", None)

    return JsonResponse({"success": True})

# Eliminar datos rellenados y variables del cronómetro en la actividad de estudio en directo
def cancel_live_study_activity(request):
    request.session.pop("live_study_form_data", None)
    request.session.pop("open_study_modal", None)
    request.session.pop("open_live_study", None)

    return JsonResponse({"success": True})

# Creación de actividad deportiva con gestión de errores en caso de fallar
# o redirigiendo a la página desde donde se hizo la petición en caso de éxito
def create_sport_activity(request):
    if request.method == "POST":
        form = SportActivityForm(request.POST)

        if form.is_valid():
            activity = form.save(commit=False)
            activity.user = models.CustomUser.objects.first()
            
            date = form.cleaned_data["date"]
            start_time = form.cleaned_data["start_time"]
            end_time = form.cleaned_data["end_time"]
            
            start_datetime = timezone.make_aware(datetime.combine(date.date(), start_time))

            end_datetime = timezone.make_aware(datetime.combine(date.date(), end_time))

            activity.date = start_datetime
            activity.duration = end_datetime - start_datetime
            
            activity.save()
            
            messages.success(request, "Actividad deportiva registrada correctamente")
            
            return redirect(request.POST.get("next", "home"))
        
        # Formulario inválido
        request.session["sport_form_data"] = request.POST.dict()
        request.session["open_sport_modal"] = True
        request.session["open_live_sport"] = False
                
        return redirect(request.POST.get("next", "home"))

    return redirect("home")

# Creación de actividad de deporte en directo y cálculo de su duración, con gestión de errores en caso de fallar
# o redirigiendo a la página desde donde se hizo la petición en caso de éxito
def create_live_sport_activity(request):
    if request.method == "POST":
        form = LiveSportActivityForm(request.POST)

        if form.is_valid():
            activity = form.save(commit=False)
            activity.user = models.CustomUser.objects.first()

            start_datetime = parse_datetime(request.POST.get("start_datetime"))

            end_datetime = parse_datetime(request.POST.get("end_datetime"))

            paused_duration = timedelta(milliseconds=int(request.POST.get("paused_duration", 0)))

            activity.date = start_datetime
            
            activity.duration = (end_datetime - start_datetime - paused_duration)

            activity.save()
            
            messages.success(request, "Actividad de deporte registrada correctamente")

            return redirect(request.POST.get("next", "home"))
        
        # Formulario inválido
        request.session["live_sport_form_data"] = request.POST.dict()
        request.session["open_sport_modal"] = True
        request.session["open_live_sport"] = True
        request.session["live_sport_finished"] = True

        return redirect(request.POST.get("next", "home"))

    return redirect("home")

# Eliminar datos rellenados en la actividad de deporte finalizada
def cancel_sport_activity(request):
    request.session.pop("sport_form_data", None)
    request.session.pop("open_sport_modal", None)

    return JsonResponse({"success": True})

# Eliminar datos rellenados y variables del cronómetro en la actividad de deporte en directo
def cancel_live_sport_activity(request):
    request.session.pop("live_sport_form_data", None)
    request.session.pop("open_sport_modal", None)
    request.session.pop("open_live_sport", None)

    return JsonResponse({"success": True})

def activity_history(request):
    user = models.CustomUser.objects.first()

    study_activities = models.StudyActivity.objects.filter(user=user)
    
    sport_activities = models.SportActivity.objects.filter(user=user)

    activities = []

    for activity in study_activities:
        activities.append({
            "type": "study",
            "activity": activity,
            "start_datetime": activity.date,
            "end_datetime": activity.date + activity.duration,
            "duration": timedelta(seconds=int(activity.duration.total_seconds())),
        })

    for activity in sport_activities:
        activities.append({
            "type": "sport",
            "activity": activity,
            "start_datetime": activity.date,
            "end_datetime": activity.date + activity.duration,
            "duration": timedelta(seconds=int(activity.duration.total_seconds())),
        })
        
    activities.sort(key=lambda activity: activity["start_datetime"], reverse=True)

    return render(request, 'activity_history.html', {
        "activities": activities,
    })
    
