from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from django.utils import timezone

# Create your models here.

class Trophy(models.Model):
    title = models.CharField(max_length=100)
    
    description = models.TextField(blank=True)

    icon = models.CharField(max_length=255, null=True, blank=True)
    
    points = models.PositiveIntegerField(default=10, validators=[MinValueValidator(10), MaxValueValidator(50)])

    is_repeatable = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Trophy"
        verbose_name_plural = "Trophies"
        
class Gender(models.TextChoices):
    MAN = 'H', 'Hombre'
    WOMEN = 'M', 'Mujer'
    OTHER = 'O', 'Otro'

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    
    birth_date = models.DateField(null=False, blank=False)
    
    gender = models.CharField(max_length=1, choices=Gender.choices, null=False, blank=False)
    
    experience_points = models.PositiveIntegerField(default=0)
    
    level = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(10)])
    
    trophies = models.ManyToManyField(Trophy, through='UserTrophy')
    
    def clean(self):
        super().clean()

        if self.birth_date is not None:
            today = timezone.now().date()

            minimum_birth_date = today - relativedelta(years=120)
            maximum_birth_date = today - relativedelta(years=16)
            
            if self.birth_date > today:
                raise ValidationError({'birth_date':'La fecha de nacimiento no puede ser futura'})

            if self.birth_date < minimum_birth_date:
                raise ValidationError({'birth_date':'La fecha de nacimiento no puede ser anterior a 120 años'})

            if self.birth_date > maximum_birth_date:
                raise ValidationError({'birth_date':'El usuario debe tener al menos 16 años'})
    
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
    
    duration = models.DurationField(validators=[MinValueValidator(timedelta(0))])
    
    date = models.DateTimeField()
    
    @property
    def end_time(self):
        return self.date + self.duration
    
    class Meta:
        verbose_name = "Activity"
        verbose_name_plural = "Activities"
    
class SubjectCategory(models.TextChoices):
    SCIENCES = 'sciences', 'Ciencias'
    SOCIALS = 'socials', 'Sociales'
    HUMANITIES = 'humanities', 'Humanidades'
    LANGUAGES = 'languages', 'Idiomas'
    PROGRAMMING = 'programming', 'Programación'
    OTHER = 'other', 'Otro'
    
class StudyType(models.TextChoices):
    THEORY = 'theory', 'Teoría'
    PRACTICE = 'practice', 'Práctica'
    OTHER = 'other', 'Otro'
    
class Subject(models.Model):
    name = models.CharField(max_length=100)
    
    subject_category = models.CharField(max_length=20, choices=SubjectCategory.choices)
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='subjects')
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'name'],
                name='unique_subject_per_user'
            )
        ]
    
    def __str__(self):
        return self.name
    
class StudyActivity(Activity):
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name='study_activities')
    
    study_type = models.CharField(max_length=10, choices=StudyType.choices)
    
    concentration = models.PositiveSmallIntegerField(validators=[MinValueValidator(0, message="La concentración debe ser mayor o igual a 0"), 
        MaxValueValidator(10, message="La concentración debe ser menor o igual a 10")])
    
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
    
    distance = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0, message="La distancia no debe ser negativa")])
    
    intensity = models.CharField(null=True, blank=True, max_length=20, choices=Intensity.choices)
    
    # Atributo derivado calculado según tipo de deporte seleccionado
    sport_category = models.CharField(max_length=20, editable=False)
    
    def clean(self):
        super().clean()
        if self.sport_type in [SportType.WEIGHTS, SportType.PILATES, SportType.YOGA] and self.distance is not None:
            raise ValidationError({'distance': 'La distancia solo puede indicarse para actividades de cardio'})

    def save(self, *args, **kwargs):
        if self.sport_type == SportType.WEIGHTS:
            self.sport_category = 'Fuerza'
        elif self.sport_type in [SportType.PILATES, SportType.YOGA]:
            self.sport_category = 'Flexibilidad'
        else:
            self.sport_category = 'Cardio'

        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "Sport activity"
        verbose_name_plural = "Sport activities"