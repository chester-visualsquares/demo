from django.db import models


class AdCampaignSettings(models.Model):
    client = models.ForeignKey('dashboard.Client')
    project = models.OneToOneField('dashboard.Project')
    start_date = models.DateField()
    end_date = models.DateField()
    cpa_target_1 = models.PositiveIntegerField()
    cpa_target_2 = models.PositiveIntegerField()
    budget = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)

    def __unicode__(self):
        return self.project.name
