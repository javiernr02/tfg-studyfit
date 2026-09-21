from django import forms
import core.models as models
from django.utils import timezone
import unicodedata
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

class RegisterForm(UserCreationForm):
    
    password1 = forms.CharField(
        label="Contraseña *",
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Contraseña"
            }
        ),
        error_messages={
            "required": "La contraseña es obligatoria"
        }
    )
    
    password2 = forms.CharField(
        label="Confirmar contraseña *",
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Confirmar contraseña"
            }
        ),
        error_messages={
            "required": "La confirmación de la contraseña es obligatoria"
        }
    )
    
    class Meta:
        model = models.CustomUser
        fields = ["first_name", "last_name", "username", "email", "birth_date", "gender", "password1", "password2"]
        labels = {
            "first_name": "Nombre",
            "last_name": "Apellido(s)",
            "username": "Nombre de usuario *",
            "email": "Email *",
            "birth_date": "Fecha de nacimiento *",
            "gender": "Género *"
        }
        error_messages = {
            "username": {
                "required": "El nombre de usuario es obligatorio"
            },
            "email": {
                "required": "El email es obligatorio"
            },
            "birth_date": {
                "required": "La fecha de nacimiento es obligatoria"
            },
            "gender": {
                "required": "El género es obligatorio"
            },
        }
        widgets = {
            "first_name": forms.TextInput(attrs={
                "placeholder": "Nombre"
            }),
            "last_name": forms.TextInput(attrs={
                "placeholder": "Apellido"
            }),
            "username": forms.TextInput(attrs={
                "placeholder": "Usuario"
            }),
            "email": forms.EmailInput(attrs={
                "placeholder": "ejemplo@email.com"
            }),
            "birth_date": forms.DateInput(attrs={
                "type": "date"
            }),
        }
        
    def clean_email(self):
        email = self.cleaned_data["email"]
        
        if models.CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("Ya existe un usuario con ese email")
        
        return email

class LoginForm(AuthenticationForm):
    
    username = forms.CharField(
        label="Nombre de usuario *",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Usuario"
            }
        ),
        error_messages={
            "required": "El nombre de usuario es obligatorio"
        }
    )
    
    password = forms.CharField(
        label="Contraseña *",
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Contraseña"
            }
        ),
        error_messages={
            "required": "La contraseña es obligatoria"
        }
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.error_messages["invalid_login"] = "El usuario o la contraseña no son correctos"
        
class StudyActivityForm(forms.ModelForm):
    start_time = forms.TimeField(
        label="Hora de inicio *",
        widget=forms.TimeInput(
            attrs={"type": "time"}
        ),
        error_messages={
            "required": "La hora de inicio es obligatoria"
        }
    )

    end_time = forms.TimeField(
        label="Hora de fin *",
        widget=forms.TimeInput(
            attrs={"type": "time"}
        ),
        error_messages={
            "required": "La hora de fin es obligatoria"
        }
    )
    
    concentration = forms.IntegerField(
        label="Concentración *",
        error_messages={
            "required": "La concentración es obligatoria"
        },
        widget=forms.NumberInput(
            attrs={
                "step": "1",
                "min": "0",
                "max": "10"
            }
        )
    )
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        
        if self.user and self.user.is_authenticated:
            self.fields["subject"].queryset = models.Subject.objects.filter(user=self.user)
        else:
            self.fields["subject"].queryset = models.Subject.objects.none()

    class Meta:
        model = models.StudyActivity
        fields = ["title", "description", "date", "start_time", "end_time", "subject", "study_type", "concentration"]
        labels = {
            "title": "Título *",
            "description": "Descripción",
            "date": "Fecha *",
            "subject": "Asignatura *",
            "study_type": "Tipo de estudio *"
        }
        error_messages = {
            "title": {
                "required": "El título es obligatorio"
            },
            "date": {
                "required": "La fecha es obligatoria"
            },
            "subject": {
                "required": "La asignatura es obligatoria"
            },
            "study_type": {
                "required": "El tipo de estudio es obligatorio"
            },
        }
        widgets = {
            "date": forms.DateInput(
                attrs={"type": "date"}
            ),
        }
        
    def clean(self):
        cleaned_data = super().clean()

        date = cleaned_data.get("date")
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")
        
        today = timezone.localdate()
        now = timezone.localtime()
        
        if date:
            date_only = date.date()
        
            if date_only > today:
                
                raise forms.ValidationError("La fecha no puede ser posterior a la fecha actual")
            
            elif date_only == today and start_time and end_time:
                
                current_time = now.time()
                
                if start_time > current_time:
                    raise forms.ValidationError("La hora de inicio no puede ser posterior a la hora actual")

                if end_time > current_time:
                    raise forms.ValidationError("La hora de fin no puede ser posterior a la hora actual")
                

            if start_time and end_time and end_time <= start_time:
                
                raise forms.ValidationError("La hora de fin debe ser posterior a la hora de inicio")
                    
        return cleaned_data

class LiveStudyActivityForm(forms.ModelForm):
    concentration = forms.IntegerField(
        label="Concentración *",
        error_messages={
            "required": "La concentración es obligatoria"
        },
        widget=forms.NumberInput(
            attrs={
                "step": "1",
                "min": "0",
                "max": "10"
            }
        )
    )
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        
        if self.user and self.user.is_authenticated:
            self.fields["subject"].queryset = models.Subject.objects.filter(user=self.user)
        else:
            self.fields["subject"].queryset = models.Subject.objects.none()
    
    class Meta:
        model = models.StudyActivity
        fields = ["title", "description", "subject", "study_type", "concentration"]
        labels = {
            "title": "Título *",
            "description": "Descripción",
            "subject": "Asignatura *",
            "study_type": "Tipo de estudio *"
        }
        error_messages = {
            "title": {
                "required": "El título es obligatorio"
            },
            "subject": {
                "required": "La asignatura es obligatoria"
            },
            "study_type": {
                "required": "El tipo de estudio es obligatorio"
            },
        }
        
class SubjectForm(forms.ModelForm):
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    class Meta:
        model = models.Subject
        fields = ["name", "subject_category"]

        labels = {
            "name": "Nombre *",
            "subject_category": "Categoría *",
        }
        error_messages = {
            "name": {
                "required": "El nombre es obligatorio"
            },
            "subject_category": {
                "required": "La categoría es obligatoria"
            },
        }
        
    def clean_name(self):
        name = self.cleaned_data["name"]
        user = self.user
        
        if not user or not user.is_authenticated:
            return name
        
        normalized_name = ''.join(
            c for c in unicodedata.normalize('NFD', name)
            if unicodedata.category(c) != 'Mn'
        ).lower().strip()

        for subject in models.Subject.objects.filter(user=user):
            subject_normalized = ''.join(
                c for c in unicodedata.normalize('NFD', subject.name)
                if unicodedata.category(c) != 'Mn'
            ).lower().strip()

            if subject_normalized == normalized_name:
                raise forms.ValidationError("Ya existe una asignatura con ese nombre")

        return name

class SportActivityForm(forms.ModelForm):
    start_time = forms.TimeField(
        label="Hora de inicio *",
        widget=forms.TimeInput(
            attrs={"type": "time"}
        ),
        error_messages={
            "required": "La hora de inicio es obligatoria"
        }
    )
    
    end_time = forms.TimeField(
        label="Hora de fin *",
        widget=forms.TimeInput(
            attrs={"type": "time"}
        ),
        error_messages={
            "required": "La hora de fin es obligatoria"
        }
    )
    
    distance = forms.FloatField(
        label="Distancia (km)",
        required=False,
        widget=forms.NumberInput(
            attrs={
                "step": "0.01",
                "min": "0"
            }
        )
    )
        
    class Meta:
        model = models.SportActivity
        fields = ["title", "description", "date", "start_time", "end_time", "sport_type", "distance", "intensity"]
        labels = {
            "title": "Título *",
            "description": "Descripción",
            "date": "Fecha *",
            "sport_type": "Tipo de deporte *",
            "intensity": "Intensidad"
        }
        error_messages = {
            "title": {
                "required": "El título es obligatorio"
            },
            "date": {
                "required": "La fecha es obligatoria"
            },
            "sport_type": {
                "required": "El tipo de deporte es obligatorio"
            },
        }
        widgets = {
            "date": forms.DateInput(
                attrs={"type": "date"}
            ),
        }
        
    def clean(self):
        cleaned_data = super().clean()

        date = cleaned_data.get("date")
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")
        
        sport_type = cleaned_data.get("sport_type")
        distance = cleaned_data.get("distance")
        
        cardio_types = [
            models.SportType.WALK,
            models.SportType.RUN,
            models.SportType.BIKE,
            models.SportType.HIIT,
        ]
        
        if sport_type in cardio_types and distance is None:
            raise forms.ValidationError("La distancia es obligatoria para actividades de cardio")
        
        today = timezone.localdate()
        now = timezone.localtime()
        
        if date:
            date_only = date.date()
        
            if date_only > today:
                
                raise forms.ValidationError("La fecha no puede ser posterior a la fecha actual")
            
            elif date_only == today and start_time and end_time:
                
                current_time = now.time()
                
                if start_time > current_time:
                    raise forms.ValidationError("La hora de inicio no puede ser posterior a la hora actual")

                if end_time > current_time:
                    raise forms.ValidationError("La hora de fin no puede ser posterior a la hora actual")
                

            if start_time and end_time and end_time <= start_time:
                
                raise forms.ValidationError("La hora de fin debe ser posterior a la hora de inicio")
                    
        return cleaned_data
        
class LiveSportActivityForm(forms.ModelForm):
    distance = forms.FloatField(
        label="Distancia (km)",
        required=False,
        widget=forms.NumberInput(
            attrs={
                "step": "0.01",
                "min": "0"
            }
        )
    )
    
    class Meta:
        model = models.SportActivity
        fields = ["title", "description", "sport_type", "distance", "intensity"]
        labels = {
            "title": "Título *",
            "description": "Descripción",
            "sport_type": "Tipo de deporte *",
            "intensity": "Intensidad"
        }
        error_messages = {
            "title": {
                "required": "El título es obligatorio"
            },
            "sport_type": {
                "required": "El tipo de deporte es obligatorio"
            },
        }
    
    def clean(self):
        cleaned_data = super().clean()
        
        sport_type = cleaned_data.get("sport_type")
        distance = cleaned_data.get("distance")
        
        cardio_types = [
            models.SportType.WALK,
            models.SportType.RUN,
            models.SportType.BIKE,
            models.SportType.HIIT,
        ]
        
        if sport_type in cardio_types and distance is None:
            raise forms.ValidationError("La distancia es obligatoria para actividades de cardio")