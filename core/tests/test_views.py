from django.test import SimpleTestCase, TestCase
import core.models as models
from datetime import timedelta
from django.utils import timezone
from django.urls import reverse
from core.views import format_duration, balance_logic, balance_logic_streak

# Archivo de tests unitarios y de integración para la app core

# Test para la utilidad en la aplicación para formatear la duración a cadena de texto
# Se prueban las diferentes posibilidades que pueden existir
class FormatDurationTest(SimpleTestCase):

    def test_none_duration(self):
        self.assertIsNone(format_duration(None))

    def test_duration_minutes(self):
        self.assertEqual(format_duration(timedelta(minutes=30)), "30min")

    def test_duration_one_hour(self):
        self.assertEqual(format_duration(timedelta(hours=1)), "1h")

    def test_duration_hours_without_minutes(self):
        self.assertEqual(format_duration(timedelta(hours=5)), "5h")

    def test_duration_hours_and_minutes(self):
        self.assertEqual(format_duration(timedelta(hours=2, minutes=30)), "2h 30min")


# Tests para la funcionalidad de registro
class RegisterViewTest(TestCase):
    
    def test_register_valid_data_creates_user_and_redirects_home(self):
        response = self.client.post(reverse("register"),
            {
                "username": "testregister",
                "email": "test@example.com",
                "birth_date": "10/04/2000",
                "gender": "H",
                "password1": "Test1234!",
                "password2": "Test1234!",
            }
        )

        self.assertRedirects(response, reverse("home"))

        self.assertTrue(models.CustomUser.objects.filter(email="test@example.com").exists())
        
        # Se comprueba que el registro autentica al usuario
        self.assertTrue(self.client.session.get("_auth_user_id"))

    def test_register_invalid_data_redirects_to_landing(self):
        response = self.client.post(reverse("register"),
            {
                "username": "testregister",
                "email": "testinvalid@example.com",
                "birth_date": "10/04/2000",
                "gender": "H",
                "password1": "test",
                "password2": "test",
            }
        )

        self.assertRedirects(response, reverse("landing"))
        
        self.assertFalse(models.CustomUser.objects.filter(email="testinvalid@example.com").exists())
    
    # Se comprueba que al haber errores en el formulario las contraseñas no se guardan en la sesión
    def test_register_does_not_store_password_form(self):
        self.client.post(reverse("register"),
            {
                "username": "testregister",
                "email": "test@example.com",
                "birth_date": "10/04/2000",
                "gender": "H",
                "password1": "test",
                "password2": "test",
            }
        )
        
        form_data = self.client.session.get("register_form_data", {})
        
        self.assertNotIn("password1", form_data)
        self.assertNotIn("password2", form_data)


# Tests para la funcionalidad de inicio de sesión
class LoginViewTest(TestCase):
    
    # Creación de usuario con el que trabajar en las pruebas
    def setUp(self):
        self.user = models.CustomUser.objects.create_user(username="test", birth_date="2000-04-10", gender="H", password="Test1234!")
        
    def test_login_valid_data_redirects_home(self):
        response = self.client.post(reverse("login"),
            {
                "username": "test",
                "password": "Test1234!",
            }
        )
        
        self.assertRedirects(response, reverse("home"))
        
        # Se comprueba que el inicio de sesión autentica al usuario
        self.assertTrue(self.client.session.get("_auth_user_id"))

    def test_login_invalid_password_redirects_to_landing(self):
        response = self.client.post(reverse("login"),
            {
                "username": "test",
                "password": "Password123!",
            }
        )
        
        self.assertRedirects(response, reverse("landing"))

        self.assertFalse(self.client.session.get("_auth_user_id"))
        
    # Se comprueba que al haber errores en el formulario las contraseñas no se guardan en la sesión
    def test_login_does_not_store_password(self):
        self.client.post(reverse("login"),
            {
                "username": "username",
                "password": "Password123!",
            }
        )
        
        form_data = self.client.session.get("login_form_data", {})
        
        self.assertNotIn("password", form_data)
        

# Test para el cálculo de la regla de balance entre estudio y deporte
# Se prueban las diferentes posibilidades que pueden existir
class BalanceLogicTest(SimpleTestCase):
    
    def test_balance_with_ratio_two(self):
        self.assertTrue(balance_logic(120, 60))

    def test_balance_with_ratio_greater_than_two(self):
        self.assertTrue(balance_logic(180, 60))
        
    def test_balance_with_ratio_less_than_two(self):
        self.assertFalse(balance_logic(100, 60))

    def test_balance_without_sport(self):
        self.assertFalse(balance_logic(120, 0))

    def test_balance_without_study(self):
        self.assertFalse(balance_logic(0, 60))
        

# Test para la funcionalidad de racha de balance
class BalanceLogicStreakTest(TestCase):
    
    # Creación de usuario y asignatura con el que trabajar en las pruebas
    def setUp(self):
        self.user = models.CustomUser.objects.create_user(username="test", birth_date="2000-04-10", gender="H", password="Test1234!")
        
        self.subject = models.Subject.objects.create(user=self.user, name="TestAsignatura", subject_category="Programación")
    
    # Creación de actividad de estudio
    def create_study_activity(self, date, minutes):
        return models.StudyActivity.objects.create(
            user=self.user,
            title="TestEstudio",
            date=date,
            subject=self.subject,
            study_type="practice",
            concentration=8,
            duration=timedelta(minutes=minutes),
        )
        
    # Creación de actividad de deporte
    def create_sport_activity(self, date, minutes):
        return models.SportActivity.objects.create(
            user=self.user,
            title="TestDeporte",
            date=date,
            sport_type="weights",
            intensity="very_high",
            duration=timedelta(minutes=minutes),
        )

    def test_no_activities(self):
        self.assertEqual(balance_logic_streak(self.user), 0)

    def test_one_balanced_day(self):
        today = timezone.now()
        
        self.create_study_activity(today, 120)
        self.create_sport_activity(today, 60)
        
        self.assertEqual(balance_logic_streak(self.user), 1)

    def test_two_consecutive_balanced_days(self):
        today = timezone.now()
        yesterday = today - timedelta(days=1)
        
        self.create_study_activity(today, 120)
        self.create_sport_activity(today, 60)
        
        self.create_study_activity(yesterday, 120)
        self.create_sport_activity(yesterday, 60)

        self.assertEqual(balance_logic_streak(self.user), 2)

    # Pérdida de racha por no cumplir un día
    def test_streak_stops(self):
        today = timezone.now()
        yesterday = today - timedelta(days=1)
        
        # Día de hoy con equilibrio
        self.create_study_activity(today, 120)
        self.create_sport_activity(today, 60)

        # Día de ayer sin equilibrio
        self.create_study_activity(yesterday, 60)
        self.create_sport_activity(yesterday, 60)

        self.assertEqual(balance_logic_streak(self.user), 1)

    # Pérdida de racha por no haber actividades un día
    def test_streak_stops_without_activities(self):
        today = timezone.now()
        two_days_ago = today - timedelta(days=2)

        # Día de hoy con equilibrio
        self.create_study_activity(today, 120)
        self.create_sport_activity(today, 60)
        
        # Ayer sin registro de actividades
        
        # Hace dos días con equilibrio
        self.create_study_activity(two_days_ago, 120)
        self.create_sport_activity(two_days_ago, 60)
        
        self.assertEqual(balance_logic_streak(self.user), 1)


# Tests para actividades
# Se establece usuario, asignatura y autenticación común para probar los tests de actividades
class ActivityTest(TestCase):
    
    def setUp(self):
        self.user = models.CustomUser.objects.create_user(username="test", email="test@email.com", birth_date="2000-04-10", gender="H", password="Test1234!")
        
        self.subject = models.Subject.objects.create(user=self.user, name="TestAsignatura", subject_category="programming")
        
        self.client.login(username="test", password="Test1234!")
    
    # Actividades realizadas con anterioridad
    
    def test_create_study_activity(self):
        response = self.client.post(reverse("create_study_activity"),
            {
                "title": "Python",
                "date": "26/05/2026",
                "start_time": "10:00",
                "end_time": "12:00",
                "subject": self.subject.id,
                "study_type": "practice",
                "concentration": 8,
                "next": "home"
            }
        )
        
        self.assertRedirects(response, reverse("home"))
        
        activity = models.StudyActivity.objects.get(title="Python")
        
        self.assertEqual(activity.user, self.user)
        self.assertEqual(activity.subject, self.subject)
        
        # Duration es el atributo que se guarda calculado a partir de las horas de inicio y fin introducidas
        self.assertEqual(activity.duration, timedelta(hours=2))
    
    def test_create_sport_activity(self):
        response = self.client.post(reverse("create_sport_activity"),
            {
                "title": "Pesas",
                "date": "28/05/2026",
                "start_time": "18:00",
                "end_time": "19:00",
                "sport_type": "weights",
                "intensity": "very_high",
                "next": "home"
            }
        )
        
        self.assertRedirects(response, reverse("home"))

        activity = models.SportActivity.objects.get(title="Pesas")
        
        self.assertIsNone(activity.distance)
        self.assertEqual(activity.user, self.user)
        
        # Duration es el atributo que se guarda calculado a partir de las horas de inicio y fin introducidas
        self.assertEqual(activity.duration, timedelta(hours=1))
    
    # Actividades en directo
    
    def test_create_live_study_activity(self):
        start = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0)
        end = start + timedelta(hours=2)
        
        response = self.client.post(reverse("create_live_study_activity"),
            {
                "title": "Python en directo",
                "start_datetime": start.isoformat(),
                "end_datetime": end.isoformat(),
                "paused_duration": "120000", # Indicado en milisegundos, son 2 minutos
                "subject": self.subject.id,
                "study_type": "practice",
                "concentration": 8,
                "next": "home"
            }
        )
        
        self.assertRedirects(response, reverse("home"))
        
        activity = models.StudyActivity.objects.get(title="Python en directo")
        
        self.assertEqual(activity.duration, timedelta(minutes=118))
        
        # Comprueba que el cálculo de la fecha se realiza correctamente
        self.assertEqual(activity.date.date(), start.date())
        
    def test_create_live_sport_activity(self):
        start = timezone.now().replace(hour=19, minute=0, second=0, microsecond=0)
        end = start + timedelta(minutes=45)
        
        response = self.client.post(reverse("create_live_sport_activity"),
            {
                "title": "Pesas en directo",
                "start_datetime": start.isoformat(),
                "end_datetime": end.isoformat(),
                "paused_duration": "180000", # Indicado en milisegundos, son 3 minutos
                "sport_type": "weights",
                "intensity": "very_high",
                "next": "home"
            }
        )
        
        self.assertRedirects(response, reverse("home"))
        
        activity = models.SportActivity.objects.get(title="Pesas en directo")
        
        self.assertIsNone(activity.distance)
        self.assertEqual(activity.duration, timedelta(minutes=42))
        
        # Comprueba que el cálculo de la fecha se realiza correctamente
        self.assertEqual(activity.date.date(), start.date())
    
    # Se crea una actividad primero para luego comprobar la edición
    def create_study_activity(self):
        return models.StudyActivity.objects.create(
            user=self.user,
            title="Estudio para editar",
            date=timezone.now(),
            subject=self.subject,
            study_type="theory",
            concentration=6,
            duration=timedelta(hours=1)
        )
    
    def test_edit_study_activity(self):
        activity = self.create_study_activity()

        response = self.client.post(reverse("edit_activity", args=[activity.id]),
            {
                "title": "Estudio para editar editado",
                "date": "19/09/2026",
                "start_time": "10:00",
                "end_time": "12:00",
                "subject": self.subject.id,
                "study_type": "practice",
                "concentration": 9,
                "next": "activity_history"
            }
        )
        
        self.assertRedirects(response, reverse("activity_history"))
        
        activity.refresh_from_db()

        self.assertEqual(activity.title, "Estudio para editar editado")
        self.assertEqual(activity.concentration, 9)
        self.assertEqual(activity.duration, timedelta(hours=2))
    
    # Se hace lo mismo para deporte, se crea una actividad primero para luego comprobar la edición
    def create_sport_activity(self):
        return models.SportActivity.objects.create(
            user=self.user,
            title="Deporte para editar",
            date=timezone.now(),
            sport_type="weights",
            intensity="very_high",
            duration=timedelta(minutes=45)
        )
    
    def test_edit_sport_activity(self):
        activity = self.create_sport_activity()

        response = self.client.post(reverse("edit_activity", args=[activity.id]),
            {
                "title": "Deporte para editar editado",
                "date": "23/09/2026",
                "start_time": "10:00",
                "end_time": "11:00",
                "sport_type": "run",
                "intensity": "high",
                "distance": "4.5",
                "next": "activity_history"
            }
        )
        
        self.assertRedirects(response, reverse("activity_history"))
        
        activity.refresh_from_db()

        self.assertEqual(activity.title, "Deporte para editar editado")
        self.assertEqual(activity.intensity, "high")
        self.assertEqual(activity.distance, 4.5)
        self.assertEqual(activity.duration, timedelta(hours=1))
    
    def test_delete_study_activity(self):
        activity = self.create_study_activity()
        
        response = self.client.post(reverse("delete_activity", args=[activity.id]),
            {
                "next": "activity_history"
            }
        )
        
        self.assertRedirects(response, reverse("activity_history"))
        
        self.assertFalse(models.Activity.objects.filter(id=activity.id).exists())
    
    def test_delete_sport_activity(self):
        activity = self.create_sport_activity()
        
        response = self.client.post(reverse("delete_activity", args=[activity.id]),
            {
                "next": "activity_history"
            }
        )
        
        self.assertRedirects(response, reverse("activity_history"))
        
        self.assertFalse(models.Activity.objects.filter(id=activity.id).exists())
    
    def test_user_cannot_delete_other_user_study_activity(self):
        # Creamos otro usuario
        other_user = models.CustomUser.objects.create_user(username="otheruser", email="otheruser@email.com", birth_date="2000-04-25", gender="M", password="Test1234!")
        
        # Creamos otra actividad
        activity = models.StudyActivity.objects.create(
            user=other_user,
            title="Actividad de otro",
            date=timezone.now(),
            subject = models.Subject.objects.create(
                user=other_user,
                name="Java",
                subject_category="programming"
            ),
            study_type="practice",
            concentration=7,
            duration=timedelta(hours=1)
        )
        
        response = self.client.post(reverse("delete_activity", args=[activity.id]))
        
        self.assertEqual(response.status_code, 404)
        self.assertTrue(models.Activity.objects.filter(id=activity.id).exists())
        
    def test_user_cannot_delete_other_user_sport_activity(self):
        # Creamos otro usuario
        other_user = models.CustomUser.objects.create_user(username="otherotheruser", email="otherother@email.com", birth_date="2000-04-26", gender="M", password="Test1234!")
        
        # Creamos otra actividad
        activity = models.SportActivity.objects.create(
            user=other_user,
            title="Actividad de otro",
            date=timezone.now(),
            sport_type="weights",
            intensity="high",
            duration=timedelta(minutes=45)
        )
        
        response = self.client.post(reverse("delete_activity", args=[activity.id]))
        
        self.assertEqual(response.status_code, 404)
        self.assertTrue(models.Activity.objects.filter(id=activity.id).exists())
        

# Se establece usuario y autenticación común para probar los tests de asignatura
class SubjectTest(TestCase):
    
    def setUp(self):
        self.user = models.CustomUser.objects.create_user(username="user", email="user@email.com", birth_date="2000-04-30", gender="M", password="Test1234!")
        
        self.client.login(username="user", password="Test1234!")
        
    def test_create_subject(self):
        response = self.client.post(reverse("create_subject"),
            {
                "name": "Gestión de proyectos",
                "subject_category": "programming"
            }
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(models.Subject.objects.filter(user=self.user).count(), 1)
        
        subject = models.Subject.objects.get(user=self.user)
        
        self.assertEqual(subject.name, "Gestión de proyectos")
    
    def test_create_invalid_subject(self):
        response = self.client.post(reverse("create_subject"),
            {
                "name": "",
                "subject_category": "programming"
            }
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_delete_subject(self):
        subject = models.Subject.objects.create(
            user=self.user,
            name="Asignatura para borrar",
            subject_category="programming"
        )
        
        response = self.client.post(reverse("delete_subject", args=[subject.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(models.Subject.objects.filter(id=subject.id).exists())
    
    def test_delete_subject_with_activities(self):
        subject = models.Subject.objects.create(
            user=self.user,
            name="Asignatura no borrable",
            subject_category="programming"
        )
        
        models.StudyActivity.objects.create(
            user=self.user,
            title="Actividad",
            date=timezone.now(),
            subject=subject,
            study_type="practice",
            concentration=7,
            duration=timedelta(hours=1)
        )
        
        response = self.client.post(reverse("delete_subject", args=[subject.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(models.Subject.objects.filter(id=subject.id).exists())
    

# Probar consulta de actividades
class ActivityConsultationTest(TestCase):
    
    def setUp(self):
        self.user = models.CustomUser.objects.create_user(username="consultationuser", email="consultationuser@email.com", birth_date="2000-04-30", gender="M", password="Test1234!")
        
        self.client.login(username="consultationuser", password="Test1234!")
    
    def test_activity_consultation_without_activities(self):
        response = self.client.get(reverse("activity_history"))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_activities_count"], 0)
    
    def test_activity_consultation(self):
        models.StudyActivity.objects.create(
            user=self.user,
            title="Actividad de estudio",
            date=timezone.now(),
            subject = models.Subject.objects.create(
                user=self.user,
                name="Java",
                subject_category="programming"
            ),
            study_type="practice",
            concentration=7,
            duration=timedelta(hours=2)
        )
        
        models.SportActivity.objects.create(
            user=self.user,
            title="Actividad de deporte",
            date=timezone.now(),
            sport_type="weights",
            intensity="high",
            duration=timedelta(minutes=45)
        )
        
        response = self.client.get(reverse("activity_history"))
                
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_activities_count"], 2)