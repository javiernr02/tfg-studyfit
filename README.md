# StudyFit

Bienvenido a StudyFit una innovadora aplicación para el seguimiento de estudio y deporte.

## Instalación ⚙️

1) git clone https://github.com/javiernr02/tfg-studyfit.git
2) Instalar Python 3.12.10 https://www.python.org/downloads/windows/
    - Configurar variable de entorno, en PATH añadir: ubicacion_python\Python\Python312\Scripts
    Añadir también en PATH: ubicacion_python\Python\Python312\
    - En cmd comprobar versión: python --version
3) Crear entorno virtual venv en la raíz del proyecto:
    - py -3.12 -m venv venv
    - venv\Scripts\activate (Para desactivarlo: deactivate)
    - Ctrl + shift + p -> Select Interpreter -> verificar que esté el de venv seleccionado
4) Instalar requisitos:
    - Actualizar instalador de paquetes pip: python.exe -m pip install --upgrade pip
    - Instalar requisitos: pip install -r requirements.txt
5) Instalación base de datos PostgreSQL 18.3 https://www.enterprisedb.com/downloads/postgres-postgresql-downloads
    - Configurar variable de entorno, en PATH añadir: ubicacion_postgresql\PostgreSQL\18\bin
    - En cmd comprobar versión: psql --version
    - Entrar en postgreSQL usando contraseña establecida en la instalación: psql -U postgres
    - Crear la base de datos: CREATE DATABASE studyfitdb;
    - Crear usuario: CREATE USER studyfituser WITH PASSWORD 'your_password';
    - Hacer propietario de la BD al usuario creado: ALTER DATABASE studyfitdb OWNER TO studyfituser;
    - Comprobar información de la BD: \l
    - Para salir de postgreSQL: \q
6) Editar archivo de configuración
    - Copiar contenido .env.example en nuevo archivo .env
    - En DB_PASSWORD poner contraseña configurada en el usuario de la BD (paso 5)
6) Preparación base de datos
    - Nos ubicamos en raíz del proyecto
    - Ejecutar migraciones detectando cambios en los modelos: python manage.py makemigrations
    - Ejecutar esos cambios y crear el schema en la BD: python manage.py migrate
    - Poblar la BD con los datos mediante el script creado: python manage.py seed
    - Si queremos eliminar los datos de la base de datos: python manage.py flush
    - Para acceder al panel de administración /admin creamos usuario escribiendo username y password: python manage.py createsuperuser
7) Ejecución de la aplicación
    - Ejecutar servidor: python manage.py runserver
    - Navegar al despliegue en local: http://127.0.0.1:8000/
    - Comprobar correcto funcionamiento de la aplicación

## Autor 👤

**Javier Nunes Ruiz** 