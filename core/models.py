from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.

class Trophy(models.Model):
    title = models.CharField(max_length=100)
    
    description = models.TextField(blank=True)

    icon = models.CharField(max_length=255, null=True, blank=True)
    
    points = models.PositiveIntegerField(default=1)

    is_repeatable = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Trophy"
        verbose_name_plural = "Trophies"

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    
    birth_date = models.DateField(null=True, blank=True)
    
    GENDER_CHOICES = [
        ('H', 'Hombre'),
        ('M', 'Mujer'),
        ('O', 'Otro'),
    ]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=False, blank=False)
    
    experience_points = models.PositiveIntegerField(default=0)
    
    level = models.PositiveIntegerField(default=1)
    
    trophies = models.ManyToManyField(Trophy, through='UserTrophy')
    
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

# Tabla intermedia para relacionar usuarios con trofeos
class UserTrophy(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='user_trophies')
    
    trophy = models.ForeignKey(Trophy, on_delete=models.CASCADE)
    
    obtained_at = models.DateTimeField()
    
    class Meta:
        verbose_name = "User trophy"
        verbose_name_plural = "User trophies"
    
class Activity(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='activities')
    
    title = models.CharField(max_length=100)
    
    description = models.TextField(blank=True)
    
    duration = models.DurationField()
    
    date = models.DateField()
    
    class Meta:
        verbose_name = "Activity"
        verbose_name_plural = "Activities"
    
class SubjectCategory(models.TextChoices):
    SCIENCES = 'sciences', 'Ciencias'
    SOCIALS = 'socials', 'Sociales'
    HUMANITIES = 'humanities', 'Humanidades'
    LANGUAGES = 'languages', 'Idiomas'
    PROGRAMMING = 'programming', 'Programación'
    
class Subject(models.Model):
    name = models.CharField(max_length=100)
    
    subjectCategory = models.CharField(max_length=20, choices=SubjectCategory.choices)
    
CONCENTRATION_CHOICES = [(i, i) for i in range(0, 11)]

class StudyActivity(Activity):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='study_activities')
    
    concentration = models.PositiveSmallIntegerField(choices=CONCENTRATION_CHOICES, 
        validators=[MinValueValidator(0), MaxValueValidator(0)])
    
    class Meta:
        verbose_name = "Study activity"
        verbose_name_plural = "Study activities"
    
class SportType(models.TextChoices):
    WALK = 'walk', 'Caminata'
    RUN = 'run', 'Carrera'
    WEIGHTS = 'weights', 'Pesas'
    BIKE = 'bike', 'Bicicleta'
    PILATES = 'pilates', 'Pilates'
    YOGA = 'yoga', 'Yoga'
    HIIT = 'hiit', 'HIIT'
    
class Intensity(models.TextChoices):
    VERY_LOW = 'very_low', 'Muy baja'
    LOW = 'low', 'Baja'
    MEDIUM = 'medium', 'Media'
    HIGH = 'high', 'Alta'
    VERY_HIGH = 'very_high', 'Muy alta'
    
class SportActivity(Activity):
    sport_type = models.CharField(max_length=20, choices=SportType.choices)
    
    distance = models.FloatField(null=True, blank=True)
    
    intensity = models.CharField(max_length=20, choices=Intensity.choices)
    
    # Atributo derivado calculado según tipo de deporte seleccionado
    sport_category = models.CharField(max_length=20, editable=False)

    def save(self, *args, **kwargs):
        if self.sport_type in ['weights']:
            self.sport_category = 'Fuerza'
        elif self.sport_type in ['pilates', 'yoga']:
            self.sport_category = 'Flexibilidad'
        else:
            self.sport_category = 'Cardio'

        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "Sport activity"
        verbose_name_plural = "Sport activities"