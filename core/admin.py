from django.contrib import admin
import core.models as models

# Register your models here.

admin.site.register(models.Trophy)
admin.site.register(models.CustomUser)
admin.site.register(models.UserTrophy)
admin.site.register(models.Activity)
admin.site.register(models.Subject)
admin.site.register(models.StudyActivity)
admin.site.register(models.SportActivity)