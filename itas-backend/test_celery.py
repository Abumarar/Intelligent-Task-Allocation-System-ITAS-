import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'itas.settings')
django.setup()

from core.tasks import parse_cv_async
try:
    print("Testing delay...")
    res = parse_cv_async.delay(1)
    print("Delay returned!", res.id)
except Exception as e:
    print("ERROR:", e)
