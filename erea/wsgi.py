import os
import sys

# إضافة مسار البيئة الافتراضية
#activate_this = 'C:/xampp/htdocs/erea/myenv/Scripts/activate_this.py'
#exec(open(activate_this).read(), dict(__file__=activate_this))

# إضافة مسار المشروع
sys.path.append('D:/مجلد جديد /erea/erea')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erea.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()