from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions
import chromedriver_autoinstaller
import core.models as models
from datetime import timedelta
import time

# Tests de interfaz mediante Selenium
class SeleniumTest(StaticLiveServerTestCase):
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Instalación de chromedriver
        chromedriver_autoinstaller.install()
        
        options = webdriver.ChromeOptions()
        options.add_argument("--window-size=1920,1080")
        
        cls.driver = webdriver.Chrome(options=options)
        cls.driver.implicitly_wait(2)
        
    def setUp(self):
        self.driver.delete_all_cookies()
        
    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()
    
    
    # Test de interfaz de registro, cierre e inicio de sesión
    def test_register_logout_and_login(self):
        driver = self.driver
        
        driver.get(self.live_server_url + "/")
        
        driver.find_element(By.XPATH, "//a[contains(text(), 'Crear mi cuenta')]").click()
        
        register_modal = driver.find_element(By.ID, "register-modal")
        
        register_modal.find_element(By.ID, "id_username").send_keys("testuser")
        register_modal.find_element(By.ID, "id_email").send_keys("testuser@email.com")
        register_date = register_modal.find_element(By.ID, "id_birth_date")
        driver.execute_script("arguments[0].value = '2000-04-20';", register_date)
        register_modal.find_element(By.ID, "id_gender").send_keys("H")
        register_modal.find_element(By.ID, "id_password1").send_keys("Fdjoijiojfj2!")
        register_modal.find_element(By.ID, "id_password2").send_keys("Fdjoijiojfj2!")
        
        register_modal.find_element(By.ID, "register-submit").click()
        
        WebDriverWait(driver, 5).until(expected_conditions.url_contains("/home"))
        
        self.assertTrue(models.CustomUser.objects.filter(username="testuser").exists())
        
        driver.find_element(By.ID, "user-button").click()
        
        driver.find_element(By.ID, "logout-button").click()
        
        WebDriverWait(driver, 5).until(expected_conditions.url_contains("/"))
        
        driver.find_element(By.ID, "login-button").click()
        
        login_modal = driver.find_element(By.ID, "login-modal")
        
        login_modal.find_element(By.ID, "id_username").send_keys("testuser")
        login_modal.find_element(By.ID, "id_password").send_keys("Fdjoijiojfj2!")
        login_modal.find_element(By.ID, "login-submit").click()
        
        WebDriverWait(driver, 5).until(expected_conditions.url_contains("/home"))
    
    
    # Test de interfaz de registro de actividad de estudio realizada con anterioridad
    def test_create_study_activity(self):
        driver = self.driver
        
        # Creamos usuario y asignatura en la base de datos
        user = models.CustomUser.objects.create_user(username="studyactivityuser", email="studyactivityuser@email.com", birth_date="2000-04-30", gender="M", password="Fdjoijiojfj2!")
        
        subject = models.Subject.objects.create(
            user=user,
            name="Programación",
            subject_category="programming"
        )
        
        driver.get(self.live_server_url + "/")
        
        driver.find_element(By.ID, "login-button").click()
                
        login_modal = driver.find_element(By.ID, "login-modal")
        
        login_modal.find_element(By.ID, "id_username").send_keys("studyactivityuser")
        login_modal.find_element(By.ID, "id_password").send_keys("Fdjoijiojfj2!")
        login_modal.find_element(By.ID, "login-submit").click()
        
        WebDriverWait(driver, 5).until(expected_conditions.url_contains("/home"))
        
        driver.find_element(By.ID, "dropdown-button").click()
        
        driver.find_element(By.ID, "study-button").click()
        
        study_modal = WebDriverWait(driver, 5).until(expected_conditions.visibility_of_element_located((By.ID, "study-modal")))
        
        study_modal.find_element(By.ID, "id_title").send_keys("Actividad de estudio")
        study_modal.find_element(By.ID, "id_description").send_keys("Realización de sesión de estudio")
        study_date = study_modal.find_element(By.ID, "id_date")
        driver.execute_script("arguments[0].value = '2026-10-01';", study_date)
        study_modal.find_element(By.ID, "id_start_time").send_keys("10:00")
        study_modal.find_element(By.ID, "id_end_time").send_keys("12:00")
        Select(study_modal.find_element(By.ID, "id_subject")).select_by_visible_text("Programación")
        Select(study_modal.find_element(By.ID, "id_study_type")).select_by_visible_text("Práctica")
        study_modal.find_element(By.ID, "id_concentration").send_keys("9")
        
        study_modal.find_element(By.ID, "study-submit").click()
        
        WebDriverWait(driver, 5).until(expected_conditions.url_contains("/home"))
        
        time.sleep(2)
        
        # Se comprueba que se ha guardado correctamente
        activities = models.StudyActivity.objects.filter(user=user, title="Actividad de estudio")
        
        self.assertTrue(activities.exists())
        
        activity = activities.first()
        
        self.assertEqual(activity.user, user)
        self.assertEqual(activity.subject, subject)
        self.assertEqual(activity.duration, timedelta(hours=2))
        
    def test_create_live_sport_activity(self):
        driver = self.driver
                
        # Creamos usuario en la base de datos
        user = models.CustomUser.objects.create_user(username="livesportactivityuser", email="livesportactivityuser@email.com", birth_date="2000-04-10", gender="H", password="Fdjoijiojfj2!")
        
        driver.get(self.live_server_url + "/")
                
        driver.find_element(By.ID, "login-button").click()
                
        login_modal = driver.find_element(By.ID, "login-modal")
        
        login_modal.find_element(By.ID, "id_username").send_keys("livesportactivityuser")
        login_modal.find_element(By.ID, "id_password").send_keys("Fdjoijiojfj2!")
        login_modal.find_element(By.ID, "login-submit").click()
        
        WebDriverWait(driver, 5).until(expected_conditions.url_contains("/home"))
        
        driver.find_element(By.ID, "dropdown-button").click()
        
        driver.find_element(By.ID, "sport-button").click()
        
        WebDriverWait(driver, 5).until(expected_conditions.visibility_of_element_located((By.ID, "sport-modal")))
        
        WebDriverWait(driver, 5).until(expected_conditions.element_to_be_clickable((By.ID, "sport-live-mode"))).click()
        
        live_sport_content = WebDriverWait(driver, 5).until(expected_conditions.visibility_of_element_located((By.ID, "sport-live-content")))
                
        live_sport_content.find_element(By.ID, "id_title").send_keys("Actividad de deporte en directo")
        live_sport_content.find_element(By.ID, "id_description").send_keys("Realización de sesión de deporte en directo")
        Select(live_sport_content.find_element(By.ID, "id_sport_type")).select_by_visible_text("Pesas")
        
        WebDriverWait(driver, 5).until(expected_conditions.element_to_be_clickable((By.ID, "sport-live-start"))).click()
        
        WebDriverWait(driver, 5).until(expected_conditions.element_to_be_clickable((By.ID, "sport-live-pause")))
        
        time.sleep(5)
        
        live_sport_content.find_element(By.ID, "sport-live-pause").click()
        
        time.sleep(3)
        
        WebDriverWait(driver, 5).until(expected_conditions.element_to_be_clickable((By.ID, "sport-live-resume"))).click()
        
        time.sleep(2)
        
        WebDriverWait(driver, 5).until(expected_conditions.element_to_be_clickable((By.ID, "sport-live-finish"))).click()
        
        WebDriverWait(driver, 5).until(expected_conditions.element_to_be_clickable((By.ID, "sport-live-submit")))
        
        Select(live_sport_content.find_element(By.ID, "id_intensity")).select_by_visible_text("Baja")
        
        live_sport_content.find_element(By.ID, "sport-live-submit").click()
        
        WebDriverWait(driver, 5).until(expected_conditions.url_contains("/home"))
        
        time.sleep(2)
        
        # Se comprueba que se ha guardado correctamente
        activities = models.SportActivity.objects.filter(user=user, title="Actividad de deporte en directo")
        
        self.assertTrue(activities.exists())
        
        activity = activities.first()
        
        self.assertEqual(activity.user, user)
        self.assertEqual(activity.sport_type, "weights")
        self.assertEqual(activity.intensity, "low")
        self.assertIsNotNone(activity.duration)
        self.assertGreater(activity.duration.total_seconds(), 0)