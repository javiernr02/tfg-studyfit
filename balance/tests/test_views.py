from django.test import TestCase
import core.models as models
from datetime import timedelta
from django.utils import timezone
from django.urls import reverse
from balance.views import get_most_productive
from django.db.models.functions import TruncDate
from core.views import format_duration
from unittest.mock import patch

# Archivo de tests de integración para la app balance

# Tests para estadísticas
# Se establece usuario y autenticación común para probar los tests
class StatsTest(TestCase):
    
    def setUp(self):
        self.user = models.CustomUser.objects.create_user(username="statsuser", email="statsuser@email.com", birth_date="2000-04-30", gender="M", password="Test1234!")
        
        self.client.login(username="statsuser", password="Test1234!")
        
    def test_stats_without_activities(self):
        response = self.client.get(reverse("stats"), {"period": "week"})
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        
        self.assertEqual(data["labels"], [])
        self.assertEqual(data["study_total_time"], 0)
        self.assertEqual(data["sport_total_time"], 0)
        self.assertEqual(data["study_percent"], 0)
        self.assertEqual(data["sport_percent"], 0)
        self.assertEqual(data["study_average"], "0min")
        self.assertEqual(data["sport_average"], "0min")
    
    def test_stats_with_activities(self):
        subject = models.Subject.objects.create(
            user=self.user,
            name="Programación",
            subject_category="programming"
        )
        
        models.StudyActivity.objects.create(
            user=self.user,
            title="Estudio",
            date=timezone.now(),
            subject=subject,
            study_type="practice",
            concentration=7,
            duration=timedelta(hours=2)
        )
        
        models.SportActivity.objects.create(
            user=self.user,
            title="Deporte",
            date=timezone.now(),
            sport_type="weights",
            intensity="high",
            duration=timedelta(minutes=45)
        )
        
        response = self.client.get(reverse("stats"), {"period": "week"})
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        
        self.assertEqual(len(data["labels"]), 1)
        self.assertEqual(data["study_total_time"], 7200) # Puesto en segundos
        self.assertEqual(data["sport_total_time"], 2700) # Puesto en segundos
        self.assertEqual(data["study_percent"], 72.7)
        self.assertEqual(data["sport_percent"], 27.3)
        self.assertEqual(data["study_average"], "2h")
        self.assertEqual(data["sport_average"], "45min")
    
    def test_stats_period(self):
        subject = models.Subject.objects.create(
            user=self.user,
            name="JavaScript",
            subject_category="programming"
        )
        
        models.StudyActivity.objects.create(
            user=self.user,
            title="Actividad reciente",
            date=timezone.now() - timedelta(days=5),
            subject=subject,
            study_type="practice",
            concentration=7,
            duration=timedelta(hours=2)
        )
        
        models.StudyActivity.objects.create(
            user=self.user,
            title="Actividad antigua",
            date=timezone.now() - timedelta(days=50),
            subject=subject,
            study_type="practice",
            concentration=7,
            duration=timedelta(hours=1)
        )
        
        response = self.client.get(reverse("stats"), {"period": "month"})
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        
        # Solo deben aparecer las actividades de los últimos 30 días, por tanto, solo la reciente (hace 5 días)
        self.assertEqual(data["study_total_time"], 7200) # Puesto en segundos
        
    def test_most_productive(self):
        subject = models.Subject.objects.create(
            user=self.user,
            name="Django",
            subject_category="programming"
        )
        
        models.StudyActivity.objects.create(
            user=self.user,
            title="Estudio productivo",
            date=timezone.now(),
            subject=subject,
            study_type="practice",
            concentration=7,
            duration=timedelta(hours=2)
        )
        
        models.SportActivity.objects.create(
            user=self.user,
            title="Deporte productivo",
            date=timezone.now(),
            sport_type="weights",
            intensity="high",
            duration=timedelta(hours=1)
        )
        
        result = get_most_productive(
            models.StudyActivity.objects.filter(user=self.user),
            models.SportActivity.objects.filter(user=self.user),
            TruncDate,
            format_duration
        )
        
        self.assertEqual(result["study_time"], "2h")
        self.assertEqual(result["sport_time"], "1h")
        self.assertEqual(result["total_time"], "3h")


# Prueba para página de trofeos

class TrophiesTest(TestCase):
    
    def setUp(self):
        self.user = models.CustomUser.objects.create_user(username="trophiesuser", email="trophiesuser@email.com", birth_date="2000-04-30", gender="M", password="Test1234!", experience_points=1500, level=2)
        
        self.client.login(username="trophiesuser", password="Test1234!")
        
    @patch("balance.views.get_trophies_data")
    @patch("balance.views.get_streak")
    def test_trophies(self, mock_streak, mock_trophies):
        mock_streak.return_value = {"streak": 3}
        
        mock_trophies.return_value = {
            "repeatable_trophies_count": 4,
            "non_repeatable_trophies": [],
            "non_repeatable_trophies_count": 0,
            "non_obtained_non_repeatable_trophies": [],
            "repeatable_student_trophy_obtained_today": True,
            "repeatable_sportsman_trophy_obtained_today": True,
            "repeatable_student_trophy": None,
            "repeatable_sportsman_trophy": None
        }
        
        response = self.client.get(reverse("balance"), {"tab": "trophies"})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["tab"], "trophies")
        self.assertEqual(response.context["level"], 2)
        self.assertEqual(response.context["experience_points"], 1500)
        
        # Cada nivel son 1000 puntos, del nivel 2 lleva 500
        self.assertEqual(response.context["current_level_xp"], 500)
        self.assertEqual(response.context["remaining_points"], 500)
        self.assertEqual(response.context["level_progress"], 50) # 50% completado de la barra de progreso
        self.assertEqual(response.context["streak"], 3)
        

# Prueba para página de análisis inteligente

class AnalysisTest(TestCase):
    
    def setUp(self):
        self.user = models.CustomUser.objects.create_user(username="analysisuser", email="analysisuser@email.com", birth_date="2000-04-30", gender="M", password="Test1234!", experience_points=1500, level=2)
        
        self.client.login(username="analysisuser", password="Test1234!")
    
    @patch("balance.views.get_hybrid_prediction")
    @patch("balance.views.get_regression_curve")
    @patch("balance.views.get_regression_curve_global")
    def test_analysis(self, mock_global_regression, mock_regression, mock_prediction):
        mock_prediction.return_value = {
            "prediction": 8.5,
            "global": 8.0,
            "personal": 8.5,
            "mode": "hybrid"
        }
        
        mock_regression.return_value = {
            "best": {
                "x": 2.0
            },
            "zone": {
                "min_x": 1.5,
                "max_x": 2.5
            },
            "max_sport_hours": 3.0
        }
        
        mock_global_regression.return_value = {
            "generated_at": "15/09/2026"
        }
        
        response = self.client.get(reverse("balance"), {"tab": "analysis"})
                
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["tab"], "analysis")
        self.assertEqual(response.context["prediction"], 8.5)
        self.assertEqual(response.context["global"], 8.0)
        self.assertEqual(response.context["personal"], 8.5)
        self.assertEqual(response.context["mode"], "hybrid")
        self.assertEqual(response.context["recommended_zone"]["min_x"], 1.5)
        self.assertEqual(response.context["recommended_zone"]["max_x"], 2.5)