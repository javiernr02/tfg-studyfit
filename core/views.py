from django.shortcuts import render
import core.models as models
from django.utils import timezone
from datetime import timedelta
from collections import defaultdict

# Create your views here.

def format_duration(duration):
    total_seconds = int(duration.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    
    if hours < 1:
        return f'{minutes}min'
    elif minutes == 0:
        return f'{hours}h'
    else:
        return f'{hours}h {minutes}min'

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
                   'sport_activities_by_sport_types_format': sport_activities_by_sport_types_format
                   })