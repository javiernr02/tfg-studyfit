from django.core.management import BaseCommand, call_command
from faker import Faker
from django.utils import timezone
from datetime import timedelta
import random
from collections import defaultdict
import core.models as models
import unicodedata
import re

fake = Faker('es_ES')

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
        self.stdout.write('Loading fixtures...')
        
        call_command('loaddata', 'populate/subjects.json')
        call_command('loaddata', 'populate/trophies.json')
        
        # Creación de usuarios
        self.stdout.write('Creating users...')

        users = []

        for _ in range(80):
            base_level = random.choices(population=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], weights=[20, 15, 15, 15, 10, 10, 5, 5, 3, 2])[0]

            xp = (base_level - 1) * 1000 + random.randint(0, 999)
                        
            gender = random.choices(models.CustomUser.GENDER_CHOICES, weights=[45, 45, 10])[0][0]
            
            if gender == 'H':
                first_name = fake.first_name_male()
            elif gender == 'M':
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
                password = 'studyfit',
                birth_date = birt_date,
                gender = gender,
                experience_points = xp,
                level = base_level
            )

            users.append(user)

        subjects = list(models.Subject.objects.all())
        trophies = list(models.Trophy.objects.all())
        
        # Creación de actividades de estudio
        self.stdout.write('Creating study activities...')
        
        options = ['Sesión', 'Actividad', 'Estudio', 'Ejercicios']

        for user in users:

            study_count = int(user.level * random.uniform(2, 6))

            last_date = timezone.now().date()

            for i in range(study_count):

                subject = random.choice(subjects)

                duration = random.randint(25, 180)

                activity_date = last_date - timedelta(days=random.randint(0, 400))

                models.StudyActivity.objects.create(
                    user = user,
                    title = f'{random.choice(options)} de {subject.name}',
                    description = fake.text(max_nb_chars=100),
                    duration = timedelta(minutes=duration),
                    date = activity_date,
                    subject = subject
                )
        
        # Creación de actividades deportivas
        self.stdout.write('Creating sport activities...')
                
        options = ['Sesión', 'Actividad', 'Mejora', 'Ejercicio']
        
        for user in users:

            sport_count = int(user.level * random.uniform(1, 4))

            for _ in range(sport_count):

                sport_type = random.choice(list(models.SportType))
                
                if sport_type.value == 'hiit':
                    intensity = models.Intensity.VERY_HIGH
                else:
                    intensity = random.choice(models.Intensity.values)

                models.SportActivity.objects.create(
                    user = user,
                    title = f'{random.choice(options)} de {sport_type.label.lower()}',
                    description = fake.text(max_nb_chars=100),
                    duration = timedelta(minutes=random.randint(20, 90)),
                    date = timezone.now().date() - timedelta(days=random.randint(0, 400)),
                    sport_type = sport_type.value,
                    distance = round(random.uniform(0, 12), 2) if sport_type.value in ['walk', 'run', 'bike', 'hiit'] else None,
                    intensity = intensity
                )
                
        # Asignación de trofeos a usuarios según sus actividades
        self.stdout.write('Assigning trophies with logic...')

        for user in users:
            
            user_study_activities = list(models.StudyActivity.objects.filter(user=user))
            user_sport_activities = list(models.SportActivity.objects.filter(user=user))
            
            user_number_study_activities = len(user_study_activities)
            user_number_sport_activities = len(user_sport_activities)
            
            # Diccionario para actividades de estudio de duraciones por día
            daily_study_durations = defaultdict(lambda: timedelta())
            
            for activity in user_study_activities:
                day = activity.date
                daily_study_durations[day] += activity.duration
            
            sorted_days_study = sorted(daily_study_durations.keys())
            
            daily_study_durations_list = [daily_study_durations[day].total_seconds() / 3600 for day in sorted_days_study]
            
            # Diccionario para actividades de deporte de duraciones por día
            daily_sport_durations = defaultdict(lambda: timedelta())
            
            for activity in user_sport_activities:
                day = activity.date
                daily_sport_durations[day] += activity.duration
            
            sorted_days_sport = sorted(daily_sport_durations.keys())
            
            daily_sport_durations_list = [daily_sport_durations[day].total_seconds() / 3600 for day in sorted_days_sport]
            
            #Asignación de trofeos definidos en populate/trophies.json según cumplan las condiciones
            if user_number_study_activities >= 1:
                self._give_trophy(user, trophies[0])  # Primer Paso
                
            streak = 0
            
            for hours in daily_study_durations_list:
                
                if hours >= 2:
                    streak += 1
                    if streak >= 5:
                        self._give_trophy(user, trophies[1])  # Disciplina
                        break
                    else:
                        streak = 0
                        
            if user_number_study_activities + user_number_sport_activities >= 20:
                self._give_trophy(user, trophies[2])  # Máquina
                
            if sum(daily_study_durations_list) >= 100:
                self._give_trophy(user, trophies[3])  # Maestro del estudio
                
            if user_number_sport_activities >= 15:
                self._give_trophy(user, trophies[4])  # Atleta
                
            if any(hours >= 8 for hours in daily_study_durations_list):
                self._give_trophy(user, trophies[5])  # Potenciando la Mente
                
            for hours in daily_study_durations_list:
                
                if hours >= 4:
                    self._give_trophy(user, trophies[6])  # Estudiante Constante
                    
            for hours in daily_sport_durations_list:
                
                if hours >= 1:
                    self._give_trophy(user, trophies[7])  # Deportista Constante

        self.stdout.write(self.style.SUCCESS('Dataset generated'))


    def _give_trophy(self, user, trophy):
        models.UserTrophy.objects.get_or_create(user=user, trophy=trophy)