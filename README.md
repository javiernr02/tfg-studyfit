# StudyFit

Bienvenido a StudyFit una innovadora aplicación para el seguimiento de estudio y deporte.

## Instalación ⚙️

1) Clonar el repositorio:

   ```bash
   git clone https://github.com/javiernr02/tfg-studyfit.git
2) Instalar Python 3.12.10 https://www.python.org/downloads/windows/
    - Configurar variable de entorno, en PATH añadir: ubicacion_python\Python\Python312\Scripts
    - Añadir también en PATH: ubicacion_python\Python\Python312\
    - En cmd comprobar versión:
      
      ```bash
      python --version
3) Crear entorno virtual venv en la raíz del proyecto:
    - Crear entorno virtual:
      
      ```bash
      py -3.12 -m venv venv
    - Activar entorno virtual (para desactivarlo: deactivate):
  
      ```bash
      venv\Scripts\activate
    - Ctrl + shift + p -> Select Interpreter -> verificar que esté el de venv seleccionado
4) Instalar requisitos:
    - Actualizar instalador de paquetes pip:
  
      ```bash
      python.exe -m pip install --upgrade pip
    - Instalar requisitos:
  
      ```bash
      pip install -r requirements.txt
5) Instalación base de datos PostgreSQL 18.3 https://www.enterprisedb.com/downloads/postgres-postgresql-downloads
    - Configurar variable de entorno, en PATH añadir: ubicacion_postgresql\PostgreSQL\18\bin
    - En cmd comprobar versión:
  
      ```bash
      psql --version
    - Entrar en postgreSQL usando contraseña establecida en la instalación:
  
      ```bash
      psql -U postgres
    - Crear la base de datos:
  
      ```sql
      CREATE DATABASE studyfitdb;
    - Crear usuario:
  
      ```sql
      CREATE USER studyfituser WITH PASSWORD 'your_password';
    - Hacer propietario de la BD al usuario creado:
  
      ```sql
      ALTER DATABASE studyfitdb OWNER TO studyfituser;
    - Comprobar información de la BD:
  
      ```sql
      \l
    - Para salir de postgreSQL:
  
      ```sql
      \q
6) Editar archivo de configuración
    - Copiar contenido .env.example en nuevo archivo .env
    - En DB_PASSWORD poner contraseña configurada en el usuario de la BD (paso 6)
7) Preparación base de datos
    - Nos ubicamos en raíz del proyecto
    - Crea archivos de migraciones por los cambios detectados en los modelos (no es necesario ejecutarlo, ya que se incluyen las migraciones por el desarrollador):
  
      ```bash
      python manage.py makemigrations
    - Aplica las migraciones generadas a la BD:
  
      ```bash
      python manage.py migrate
    - Poblar la BD con los datos, usando el script aleatorio y reproducible mediante seed fijado creado (esperar hasta que se muestre mensaje de confirmación):

      ```bash
      python manage.py seed
    - Si queremos eliminar los datos de la base de datos:
  
      ```bash
      python manage.py flush
    - Para acceder al panel de administración /admin creamos usuario escribiendo los datos que queramos para username, email y password:
  
      ```bash
      python manage.py createsuperuser
8) Entrenamiento del modelo de IA
    - Ejecutar el siguiente comando (esperar hasta que se muestre mensaje de confirmación) para que se genere el archivo en la carpeta del proyecto 'ai_models':

      ```bash
      python manage.py train_model
9) Ejecución de la aplicación
    - Ejecutar servidor:
  
      ```bash
      python manage.py runserver
    - Navegar al despliegue en local: http://127.0.0.1:8000/
    - Comprobar el correcto funcionamiento de la aplicación

## Autor 👤

**Javier Nunes Ruiz** 
