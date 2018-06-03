import json

from django.apps import apps
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Count
from django.db.models.fields import FieldDoesNotExist


class Client (models.Model):
    TZNAME_CHOICES = (
        (u'Asia/Hong_Kong', u'Asia/Hong_Kong (GMT +08:00)'),
        (u'Etc/UTC', u'Etc/UTC (GMT +00:00)'),
    )

    name = models.CharField(max_length=32)
    timezone = models.CharField(max_length=32, choices=TZNAME_CHOICES,
                                default='Asia/Hong_Kong')
    daily_report_required = models.BooleanField(default=True)
    country_breakdown_required = models.BooleanField(default=True)
    signup_list_required = models.BooleanField(default=True)

    def __unicode__(self):
        return self.name


class UserProfile(models.Model):
    TZNAME_CHOICES = (
        (u'Asia/Hong_Kong', u'Asia/Hong_Kong (GMT +08:00)'),
        (u'Etc/UTC', u'Etc/UTC (GMT +00:00)'),
    )

    user = models.OneToOneField(User, related_name='profile')
    client = models.ForeignKey('Client', blank=True, null=True)
    timezone = models.CharField(max_length=32, choices=TZNAME_CHOICES,
                                default='Asia/Hong_Kong')


# TODO(chesterwu): Introduce ProjectGroup concept
class Project(models.Model):
    NETWORK_CHOICES = (
        (u'FB', u'Facebook'),
        (u'LN', u'LinkedIn'),
        (u'TW', u'Twitter'),
    )

    client = models.ForeignKey('Client')
    name = models.CharField(max_length=128)
    network = models.CharField(max_length=16, choices=NETWORK_CHOICES,
                               default='FB')
    model_path = models.CharField(max_length=128, blank=True)
    # For signup list filtering for multiple fairs.
    queryset_filters = models.CharField(max_length=64, blank=True,
                                        default='{}')
    country_field_name = models.CharField(max_length=32, blank=True)
    cs_id = models.CharField(max_length=16, blank=True)
    # For SQL LIKE operator.
    gid_pattern = models.CharField(max_length=32, blank=True)
    aid_pattern = models.CharField(max_length=32, blank=False)
    non_cn_url_eng = models.URLField(max_length=128, blank=True)
    non_cn_url_chi = models.URLField(max_length=128, blank=True)
    cn_url = models.URLField(max_length=128, blank=True)
    # For SQL GROUP BY clause.
    unique_by = models.CharField(max_length=32, blank=True, default=None)
    attribution_window = models.IntegerField(blank=True, null=True,
                                             default=None)
    cs_daily_sync_required = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    last_update = models.DateTimeField()


    def __unicode__(self):
        return self.name

    @property
    def app_model(self):
        return apps.get_model(*self.model_path.split('.'))

    @property
    def countrystats_set(self):
        model_mngr = self.app_model.objects
        return model_mngr.filter(**self.queryset_filters_dict) \
            .values(self.country_field_name).annotate(count=Count('id')) \
            .order_by('-count')

    # TODO(chesterwu): Remove is_xxxx() methods after introducing ProjectGroup
    @property
    def is_facebook(self):
        return self.network == 'FB'

    @property
    def is_linkedin(self):
        try:
            self.app_model._meta.get_field_by_name('is_linkedin')
        except FieldDoesNotExist:
            return False

        return True

    @property
    def is_wechat(self):
        try:
            self.app_model._meta.get_field_by_name('is_wechat')
        except FieldDoesNotExist:
            return False

        return True

    @property
    def is_twitter(self):
        try:
            self.app_model._meta.get_field_by_name('is_twitter')
        except FieldDoesNotExist:
            return False

        return True

    @property
    def queryset_filters_dict(self):
        return json.loads(self.queryset_filters)


class AdStats(models.Model):
    project = models.ForeignKey('Project')
    impressions = models.PositiveIntegerField()
    clicks = models.PositiveIntegerField()
    link_clicks = models.PositiveIntegerField(null=True)
    spent = models.PositiveIntegerField()  # in cent
    conversions = models.PositiveIntegerField()

    class Meta:
        abstract = True

    @property
    def dollar_spent(self):
        return float(self.spent) / 100

    @property
    def dollar_cpa(self):
        if self.conversions == 0:
            return None
        return float(self.spent) / self.conversions / 100

    @property
    def ctr(self):
        if self.impressions == 0:
            return None
        return float(self.clicks) / self.impressions

    @property
    def website_ctr(self):
        if self.impressions == 0 or self.link_clicks is None:
            return None
        return float(self.link_clicks) / self.impressions

    @property
    def cpc(self):
        if self.clicks == 0:
            return None
        return float(self.spent) / self.clicks / 100

    @property
    def cplc(self):
        if self.link_clicks == 0 or self.link_clicks is None:
            return None
        return float(self.spent) / self.link_clicks / 100

    @property
    def conversion_rate(self):
        if self.link_clicks == 0 or self.link_clicks is None:
            return None
        return float(self.conversions) / self.link_clicks

    @property
    def cpa_class(self):
        CPA_HIGH = 'cpa-high'
        CPA_MEDIUM = 'cpa-medium'
        CPA_LOW = 'cpa-low'
        CPA_NA = 'cpa-na'

        target_1 = self.project.adcampaignsettings.cpa_target_1
        target_2 = self.project.adcampaignsettings.cpa_target_2

        if not self.conversions and not self.dollar_spent:
            return CPA_NA
        elif target_2 <= self.dollar_cpa or not self.conversions:
            return CPA_HIGH
        elif target_1 <= self.dollar_cpa:
            return CPA_MEDIUM
        elif 0 <= self.dollar_cpa < target_1:
            return CPA_LOW
        else:
            return CPA_NA

    def __unicode__(self):
        return '%s - %s' % self.project.name


class WeeklyAdStats(AdStats):
    # A local date of the ad stats that follows the client's timezone setting.
    start_date = models.DateField()

    class Meta:
        abstract = True

    def __unicode__(self):
        return '%s - %s' % (self.project.name, self.start_date)


class DailyAdStats(AdStats):
    # A local date of the ad stats that follows the client's timezone setting.
    date = models.DateField()

    class Meta:
        unique_together = ('project', 'date')

    def __unicode__(self):
        return '%s - %s' % (self.project.name, self.date)


class Channel(models.Model):
    NETWORK_CHOICES = (
        (u'FB', u'Non-China'),
        (u'WE', u'China'),
    )
    LANGUAGES_CHOICES = (
        (u'CHI', u'Chinese'),
        (u'ENG', u'English'),
        (u'SC', u'Simplified Chinese'),
    )

    project = models.ForeignKey('Project')
    name = models.CharField(max_length=64)
    aid = models.CharField(max_length=16)
    network = models.CharField(max_length=2, choices=NETWORK_CHOICES,
                               default='FB')
    language = models.CharField(max_length=4, choices=LANGUAGES_CHOICES,
                                default='CHI')
    short_url = models.URLField(max_length=128)
