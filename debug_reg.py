import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE","project.settings")
django.setup()
from django.test import Client
from django.urls import reverse
from apps.users.models import User
c = Client()
before = User.objects.count()
r = c.post(reverse('users:register'), {
    'username':'dbguser','first_name':'Dbg','last_name':'User',
    'email':'dbg@example.com','password1':'StrongPass123!','password2':'StrongPass123!',
    'terms':'on'
})
after = User.objects.count()
print('status', r.status_code, getattr(r,'url',None))
print('count before/after', before, after)
print('user exists', User.objects.filter(username='dbguser').exists())
# session auth
print('authenticated client?', c.get(reverse('users:profile')).status_code)
u = User.objects.filter(username='dbguser').first()
if u: u.delete()
