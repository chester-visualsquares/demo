from django.db import models


class AdCampaign(models.Model):
    fbid = models.CharField(max_length=32)
    project = models.OneToOneField('dashboard.Project')
    ad_account = models.ForeignKey('AdAccount')
    is_active = models.BooleanField(default=False)

    def __unicode__(self):
        return self.fbid


class AdAccount(models.Model):
    fbid = models.CharField(max_length=32)
    client = models.ForeignKey('dashboard.Client')
    admin_user_id = models.CharField(max_length=32)
    access_token = models.CharField(max_length=256)

    def __unicode__(self):
        return self.fbid
