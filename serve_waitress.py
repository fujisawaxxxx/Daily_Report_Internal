import os
os.chdir(r"C:\srv\Daily_Report_Internal")
from waitress import serve
from config.wsgi import application
serve(application, listen="127.0.0.1:8001")
