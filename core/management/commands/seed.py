from django.core.management import BaseCommand, call_command
from faker import Faker
from django.utils import timezone
from datetime import timedelta, datetime, time
import random
from collections import defaultdict
import core.models as models
import unicodedata
import re
from statistics import median
import json
SEED = 2026
random.seed(SEED)

fake = Faker('es_ES')
Faker.seed(SEED)
fake.seed_instance(SEED)

def clean_text(text):
    # Quitar tildes
    text = ''.join(i for i in unicodedata.normalize('NFD', text) if unicodedata.category(i) != 'Mn')
    
    # Minúsculas y eliminar todo lo que no sea letra o número
    text = re.sub(r'[^a-z0-9]', '', text.lower())
    return text

# Poblar base de datos con lógica
class Command(BaseCommand):
    help = 'Realistic seed with logic'

    def handle(self, *args, **kwargs):
        
        # Carga de datos fixtures
        self.stdout.write('Loading fixture...')
        
        call_command('loaddata', 'populate/trophies.json')
        
        # Creación de usuarios
        self.stdout.write('Creating users...')

        users = []

        for i in range(200):
            
            # Nivel máximo para probar funcionalidades y que los datos del perfil tengan sentido
            if i == 0 or i == 1 or i == 2:
                base_level = 10
                
            else:
                base_level = random.choices(population=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], weights=[20, 15, 15, 15, 10, 10, 5, 5, 3, 2])[0]
                
            xp = (base_level - 1) * 1000 + random.randint(0, 999)
                        
            gender = random.choices(list(models.Gender), weights=[45, 45, 10])[0]
            
            if gender == models.Gender.MAN:
                first_name = fake.first_name_male()
            elif gender == models.Gender.WOMEN:
                first_name = fake.first_name_female()
            else:
                first_name = fake.first_name()
            
            last_name = fake.last_name()
            
            username = f'{clean_text(first_name)}{clean_text(last_name)}{random.randint(100,999)}'
            
            age_range = random.choices([(18, 30), (31, 50), (51, 64), (65, 80), (81, 100), (101, 120)], weights=[35, 30, 20, 10, 4, 1])[0]
            
            min_age, max_age = age_range
            birt_date = fake.date_of_birth(minimum_age=min_age, maximum_age=max_age)
            
            user = models.CustomUser.objects.create_user(
                first_name = first_name,
                last_name = last_name,
                username = username,
                email = f'{username}@email.com',
                password = 'Studyfit1!',
                birth_date = birt_date,
                gender = gender.value,
                experience_points = xp,
                level = base_level
            )

            users.append(user)
        
        # Guardamos los últimos 100 usuarios para pruebas de carga
        with open("populate/locust_users.json", "w", encoding="utf-8") as file:
            json.dump(
                [user.username for user in users[-100:]],
                file,
                ensure_ascii=False,
                indent=4
            )
            
        with open("populate/subjects.json", encoding="utf-8") as file:
            subject_data = json.load(file)

        for user in users:
            for subject in subject_data:
                models.Subject.objects.create(
                    user=user,
                    name=subject["name"],
                    subject_category=subject["subject_category"]
                )
                
        trophies = list(models.Trophy.objects.all())
        
        days = [timezone.now().date() - timedelta(days=i) for i in range(400)]
        
        # Creación de actividades deportivas
        self.stdout.write('Creating sport activities...')
                    
        options = ['Sesión', 'Actividad', 'Mejora', 'Ejercicio']
        
        sport_by_day = {}
        sport_activities_by_day = {}
        
        for user in users:
            
            sport_by_day[user.id] = {}
            sport_activities_by_day[user.id] = {}
            
            for i in days:
                
                sport_probability = min(0.9, 0.1 + user.level * 0.07)
                
                if i.weekday() >= 5:
                    sport_probability = min(0.9, sport_probability + 0.2)
                
                if random.random() < sport_probability:
                    
                    sport_type = random.choice(list(models.SportType))
                    
                    if sport_type.value == 'hiit':
                        intensity = models.Intensity.VERY_HIGH
                    else:
                        intensity = random.choice(models.Intensity.values)
                    
                    minutes_range = random.choices([(10, 29), (30, 59), (60, 99), (100, 120)], weights=[10, 60, 20, 10])[0]
                    minutes = random.randint(minutes_range[0], minutes_range[1])
                    
                    sport_hour = random.randint(7, 17)
                    sport_minute = random.randint(0, 59)
                    
                    sport_datetime = timezone.make_aware(datetime.combine(i, time(sport_hour, sport_minute)))
                    
                    sport_activities_by_day[user.id][i] = (sport_activities_by_day[user.id].get(i, 0) + minutes)
                    sport_by_day[user.id][i] = (sport_datetime, intensity)
                    
                    models.SportActivity.objects.create(
                        user = user,
                        title = f'{random.choice(options)} de {sport_type.label.lower()}',
                        description = fake.text(max_nb_chars=100),
                        duration = timedelta(minutes=minutes),
                        date = sport_datetime,
                        sport_type = sport_type.value,
                        distance = round(random.uniform(0, 12), 2) if sport_type.value in ['walk', 'run', 'bike', 'hiit'] else None,
                        intensity = intensity
                    )
        
        # Creación de actividades de estudio
        self.stdout.write('Creating study activities...')
        
        options = ['Sesión', 'Actividad', 'Estudio', 'Ejercicios']

        for user in users:
            
            for i in days:
                
                study_probability = min(0.9, 0.1 + user.level * 0.08)
                
                if i.weekday() >= 5:
                    study_probability = max(0.1, study_probability - 0.2)
                
                if random.random() < study_probability:
                    
                    study_activities_level_weights = {
                        1: ([1, 2], [0.9, 0.1]),
                        2: ([1, 2], [0.8, 0.2]),
                        3: ([1, 2], [0.7, 0.3]),
                        4: ([1, 2, 3], [0.45, 0.4, 0.15]),
                        5: ([1, 2, 3], [0.25, 0.5, 0.25]),
                        6: ([1, 2, 3], [0.05, 0.6, 0.35]),
                        7: ([2, 3, 4], [0.3, 0.5, 0.2]),
                        8: ([2, 3, 4], [0.1, 0.6, 0.3]),
                        9: ([2, 3, 4, 5], [0.15, 0.4, 0.3, 0.15]),
                        10: ([2, 3, 4, 5], [0.05, 0.2, 0.45, 0.3]),
                    }
                    
                    choices, weights = study_activities_level_weights[user.level]
                    
                    study_activities_by_day = random.choices(choices, weights=weights)[0]
                    
                    sport_info = sport_by_day[user.id].get(i)
                    
                    if sport_info:
                        sport_datetime, sport_intensity = sport_info
                    else:
                        sport_datetime = None
                        sport_intensity = None
                    
                    sport_minutes = sport_activities_by_day[user.id].get(i, 0)
                    
                    subjects = list(models.Subject.objects.filter(user=user))
                    
                    for activity_by_day in range(study_activities_by_day):
                        subject = random.choice(subjects)
                        
                        duration_range = random.choices([(20, 44), (45, 74), (75, 100)], weights=[20, 50, 30])[0]
                        duration = random.randint(duration_range[0], duration_range[1])
                        
                        if sport_datetime:
                            
                            max_hours_until_end_day = 23 - sport_datetime.hour
                            possible_differences = [1, 2, 3, 4, 5, 6]
                            
                            valid_differences = [d for d in possible_differences if d <= max_hours_until_end_day]
                            
                            if valid_differences:
                                
                                if user == users[0]:
                                    difference = min(valid_differences)
                                    
                                elif user == users[1]:
                                    difference = median(valid_differences)
                                    
                                elif user == users[2]:
                                    difference = max(valid_differences)
                                    
                                else:
                                    difference = random.choice(valid_differences)
                                    
                            else:
                                difference = 1
                                
                            study_datetime = sport_datetime + timedelta(minutes=sport_minutes) + timedelta(hours=difference)
                                
                        else:
                            study_datetime = timezone.make_aware(datetime.combine(i, time(random.randint(7, 21), random.randint(0, 59))))
                            
                        # Tipo de estudio
                        study_type = random.choices(population=list(models.StudyType), weights=[49, 45, 6])[0]
                        
                        # Usuario con concentración predeterminada para probar funcionalidades
                        if user == users[0]:
                            concentration = 8
                        
                        # Usuario con concentraciones altas
                        elif user == users[1]:    
                            concentration = min(10, int(random.randint(7, 10) + (sport_minutes / 120)))
                            
                        # Usuario con concentraciones bajas
                        elif user == users[2]:    
                            concentration = min(10, int(random.randint(1, 4) - (sport_minutes / 120)))
                        
                        # Resto de usuarios con concentraciones normales variables
                        else:
                            fatigue = activity_by_day // 2
                            
                            if sport_minutes == 0:
                                if duration < 60:
                                    concentration = max(2, random.randint(3, 6) - fatigue)
                                else:
                                    concentration = max(2, random.randint(3, 6) - (1 + fatigue))
                            
                            else:
                                if sport_minutes <= 10:
                                    concentration = max(3, random.randint(4, 6) - fatigue)
                                elif sport_minutes <= 30:
                                    concentration = max(4, random.randint(5, 8) - fatigue)
                                elif sport_minutes <= 90:
                                    concentration = max(6, random.randint(7, 10) - fatigue)
                                else:
                                    if sport_intensity == models.Intensity.VERY_HIGH:
                                        fatigue += 1
                                    concentration = max(5, random.randint(6, 8) - fatigue)
                                    
                        models.StudyActivity.objects.create(
                            user = user,
                            title = f'{random.choice(options)} de {subject.name}',
                            description = fake.text(max_nb_chars=100),
                            duration = timedelta(minutes=duration),
                            date = study_datetime,
                            subject = subject,
                            study_type=study_type.value,
                            concentration = concentration
                        )
                        
        # Asignación de trofeos a usuarios según sus actividades
        self.stdout.write('Assigning trophies with logic...')

        for user in users:
            
            user_study_activities = list(models.StudyActivity.objects.filter(user=user).order_by('date'))
            user_sport_activities = list(models.SportActivity.objects.filter(user=user).order_by('date'))
            
            user_number_study_activities = len(user_study_activities)
            user_number_sport_activities = len(user_sport_activities)
            
            user_activities = sorted(user_study_activities + user_sport_activities, key=lambda x: x.date)
            
            user_number_activities = len(user_activities)
            
            # Diccionario para actividades de estudio de duraciones por día
            daily_study_durations = defaultdict(lambda: timedelta())
            
            for activity in user_study_activities:
                day = activity.date
                daily_study_durations[day] += activity.duration
            
            sorted_days_study = sorted(daily_study_durations.keys())
            
            # daily_study_durations_list = [daily_study_durations[day].total_seconds() / 3600 for day in sorted_days_study]
            
            # Diccionario para actividades de deporte de duraciones por día
            daily_sport_durations = defaultdict(lambda: timedelta())
            
            for activity in user_sport_activities:
                day = activity.date
                daily_sport_durations[day] += activity.duration
            
            sorted_days_sport = sorted(daily_sport_durations.keys())
            
            # daily_sport_durations_list = [daily_sport_durations[day].total_seconds() / 3600 for day in sorted_days_sport]
            
            daily_total_durations = defaultdict(lambda: timedelta())
            
            for activity in user_study_activities:
                daily_total_durations[activity.date] += activity.duration
                
            for activity in user_sport_activities:
                daily_total_durations[activity.date] += activity.duration
                
            valid_days = sorted([day for day, duration in daily_total_durations.items() if duration.total_seconds() / 3600 >= 2])
            
            #Asignación de trofeos definidos en populate/trophies.json según cumplan las condiciones
            if user_number_activities >= 1:
                self._give_trophy(user, trophies[0], user_activities[0].date)  # Primer Paso
                
            streak = 1
            
            for i in range(1, len(valid_days)):
                
                if (valid_days[i] - valid_days[i - 1]).days == 1:
                    streak += 1
                else:
                    streak = 1
                    
                if streak >= 5:
                    self._give_trophy(user, trophies[1], valid_days[i])  # Disciplina
                    
                    break
                
            if user_number_study_activities + user_number_sport_activities >= 20:
                
                self._give_trophy(user, trophies[2], user_activities[19].date)  # Máquina
                
            acc_hours = 0
            
            for activity in user_study_activities:
                acc_hours += activity.duration.total_seconds() / 3600
                   
                if acc_hours >= 100:
                    
                    self._give_trophy(user, trophies[3], activity.date)  # Maestro del estudio
                    
                    break
                
            if user_number_sport_activities >= 15:
                self._give_trophy(user, trophies[4], user_sport_activities[14].date)  # Atleta
                
            for day in sorted_days_study:
                
                hours = daily_study_durations[day].total_seconds() / 3600
                
                if hours >= 8:
                    self._give_trophy(user, trophies[5], day)  # Potenciando la Mente
                    
                    break
                
            for day in sorted_days_study:
                
                hours = daily_study_durations[day].total_seconds() / 3600
                
                if hours >= 4:
                    self._give_trophy(user, trophies[6], day)  # Estudiante Constante
                    
            for day in sorted_days_sport:
                
                hours = daily_sport_durations[day].total_seconds() / 3600
                
                if hours >= 1:
                    self._give_trophy(user, trophies[7], day)  # Deportista Constante

        self.stdout.write(self.style.SUCCESS('Dataset generated'))


    def _give_trophy(self, user, trophy, date):
        
        if isinstance(date, datetime):
            aware_datetime = date
        else:
            aware_datetime = timezone.make_aware(datetime.combine(date, datetime.min.time()))
            
        models.UserTrophy.objects.get_or_create(user=user, trophy=trophy, defaults={"obtained_at": aware_datetime})