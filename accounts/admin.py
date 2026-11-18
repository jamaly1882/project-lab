from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import City,Profile
admin.site.register( City)
admin.site.register( Profile)


# Register your models here.
