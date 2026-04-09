import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blogproject.settings')
django.setup()
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@college.edu', 'admin123')
    print('Superuser created: admin / admin123')
else:
    print('Superuser already exists.')
