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
from django.core.paginator import Paginator


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

# Renderización de la página principal o de la página de landing según el usuario esté autenticado o no
def landing(request):
    
    if request.user.is_authenticated:
        return redirect('home')

    return render(request, 'landing.html')
    
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
                
    today_study_durations_format = format_duration(study_durations)
    today_sport_durations_format = format_duration(sport_durations)
        
    return {
        'today_study_activities': today_study_activities,
        'today_sport_activities': today_sport_activities,
        'today_study_durations_format': today_study_durations_format,
        'today_sport_durations_format': today_sport_durations_format,
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

# Consultar actividades registradas por el usuario mostradas según paginación pudiendo
# navegar entre las distintas páginas. Además, se pueden filtrar según distintos parámetros,
# mostrando el número de actividades encontradas
def activity_history(request):
    user = models.CustomUser.objects.first()

    study_activities = models.StudyActivity.objects.filter(user=user)
    
    sport_activities = models.SportActivity.objects.filter(user=user)
    
    subjects = models.Subject.objects.filter(user=user)
    
    edit_activity_id = request.session.pop("edit_activity_id", None)
    edit_activity_errors = request.session.pop("edit_activity_errors", None)
    scroll_activity_id = request.session.pop("scroll_activity_id", None)
    
    # Parámetros de filtros

    activity_type = request.GET.get("type", "all")
    sort = request.GET.get("sort", "newest")

    subject_id = request.GET.get("subject")
    study_type = request.GET.get("study_type")

    concentration_min = request.GET.get("concentration_min")
    concentration_max = request.GET.get("concentration_max")

    sport_type = request.GET.get("sport_type")

    distance_min = request.GET.get("distance_min")
    distance_max = request.GET.get("distance_max")

    intensity = request.GET.get("intensity")

    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")
    
    # Filtros por tipo de actividad
    
    if activity_type == "study":
        sport_activities = models.SportActivity.objects.none()
        
    elif activity_type == "sport":
        study_activities = models.StudyActivity.objects.none()
        
    # Filtros de estudio

    if activity_type == "study":
        if subject_id:
            study_activities = study_activities.filter(subject_id=subject_id)

        if study_type:
            study_activities = study_activities.filter(study_type=study_type)

        if concentration_min:
            study_activities = study_activities.filter(concentration__gte=concentration_min)
            
        if concentration_max:
            study_activities = study_activities.filter(concentration__lte=concentration_max)
    
    # Filtros de deporte

    if activity_type == "sport":
        if sport_type:
            sport_activities = sport_activities.filter(sport_type=sport_type)
            
        if intensity:
            sport_activities = sport_activities.filter(intensity=intensity)

        if distance_min:
            sport_activities = sport_activities.filter(distance__gte=distance_min)

        if distance_max:
            sport_activities = sport_activities.filter(distance__lte=distance_max)
            
    # Filtros de fechas

    if date_from:
        start_datetime = timezone.make_aware(datetime.combine(datetime.strptime(date_from, "%Y-%m-%d").date(), datetime.min.time()))
        
        study_activities = study_activities.filter(date__gte=start_datetime)
        
        sport_activities = sport_activities.filter(date__gte=start_datetime)

    if date_to:
        
        end_datetime = timezone.make_aware(datetime.combine(datetime.strptime(date_to, "%Y-%m-%d").date() + timedelta(days=1), datetime.min.time()))
        
        study_activities = study_activities.filter(date__lt=end_datetime)
        
        sport_activities = sport_activities.filter(date__lt=end_datetime)
        
    
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
        
    # Filtros de ordenación
    
    if sort == "oldest":
        activities.sort(key=lambda activity: activity["start_datetime"])
    else:
        activities.sort(key=lambda activity: activity["start_datetime"], reverse=True)
        
    # Contador
    
    total_activities_count = len(activities)
    
    # Paginación
    
    paginator = Paginator(activities, 100)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    query_params = request.GET.copy()
    
    if "page" in query_params:
        query_params.pop("page")
        
    query = query_params.urlencode()
    
    current_page = page_obj.number
    total_pages = paginator.num_pages
    
    page_numbers = []
    
    for num in range(1, total_pages + 1):
        
        if (num <= 2 or num > total_pages - 2 or abs(num - current_page) <= 1):
            page_numbers.append(num)
            
    display_pages = []
    
    for i, num in enumerate(page_numbers):
        
        if i > 0 and num > page_numbers[i - 1] + 1:
            display_pages.append("...")
            
        display_pages.append(num)

    return render(request, 'activity_history.html', {
        'page_obj': page_obj,
        'display_pages': display_pages,
        'subjects': subjects,
        'total_activities_count': total_activities_count,
        
        'activity_type': activity_type,
        'sort': sort,
        'subject_id': subject_id,
        'study_type': study_type,
        'concentration_min': concentration_min,
        'concentration_max': concentration_max,
        'sport_type': sport_type,
        'distance_min': distance_min,
        'distance_max': distance_max,
        'intensity': intensity,
        'date_from': date_from,
        'date_to': date_to,
        'query': query,
        
        'study_type_choices': models.StudyType.choices,
        'sport_type_choices': models.SportType.choices,
        'intensity_choices': models.Intensity.choices,
        
        'edit_activity_id': edit_activity_id,
        'edit_activity_errors': edit_activity_errors,
        'scroll_activity_id': scroll_activity_id
    })
    
# Editar los datos de una actividad registrada, gestionando los errores si no fuera posible actualizarla
def edit_activity(request, activity_id):
    
    activity = get_object_or_404(
        models.Activity,
        id=activity_id,
        user=models.CustomUser.objects.first()
    )

    if hasattr(activity, "studyactivity"):
        activity = activity.studyactivity
        form_class = StudyActivityForm

    elif hasattr(activity, "sportactivity"):
        activity = activity.sportactivity
        form_class = SportActivityForm

    else:
        return redirect("activity_history")

    if request.method == "POST":

        form = form_class(
            request.POST,
            instance=activity
        )

        if form.is_valid():
            activity = form.save(commit=False)
            
            date = form.cleaned_data["date"]
            start_time = form.cleaned_data["start_time"]
            end_time = form.cleaned_data["end_time"]
            
            start_datetime = timezone.make_aware(datetime.combine(date.date(), start_time))

            end_datetime = timezone.make_aware(datetime.combine(date.date(), end_time))

            activity.date = start_datetime
            activity.duration = end_datetime - start_datetime

            activity.save()
            
            request.session["scroll_activity_id"] = activity.id
            
            messages.success(request, "Actividad actualizada correctamente")
        else:
            request.session["edit_activity_errors"] = {
                "activity_id": activity.id,
                "errors": form.errors.get_json_data()
            }
            
            request.session["edit_activity_id"] = activity.id

    return redirect(request.POST.get("next", "activity_history"))

# Eliminar actividad registrada
def delete_activity(request, activity_id):
    
    if request.method == "POST":

        activity = get_object_or_404(
            models.Activity,
            id=activity_id,
            user=models.CustomUser.objects.first()
        )

        activity.delete()
        
        messages.success(request, "Actividad eliminada correctamente")
        
    return redirect(request.POST.get("next", "activity_history"))
    
