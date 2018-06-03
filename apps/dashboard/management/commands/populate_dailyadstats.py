import logging
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
import pytz

from advert.models import AdAccount
from dashboard.models import DailyAdStats, Project
from dashboard.utils import cs_get_conversions, facebook_campaign_stats

logger = logging.getLogger('django.command')


class Command(BaseCommand):
    args = '<client id> <date:YYYY-MM-DD>'
    help = ('Create a DailyAdStats record by retrieving ad spent data '
            'from FB Ads API and conversion data from CS signup table.')

    def handle(self, client_id, date_str, **options):
        ad_account = AdAccount.objects.get(client_id=client_id)
        adcampaign_set = ad_account.adcampaign_set.filter(is_active=True)

        dt_local = datetime.strptime(date_str, '%Y-%m-%d')
        dt_local = timezone.make_aware(dt_local, pytz.timezone(
            ad_account.client.timezone))

        for adcampaign in adcampaign_set:
            project = adcampaign.project
            if project.network == 'FB':
                try:
                    adcampaign_stats = facebook_campaign_stats(
                        adcampaign, date_str, date_str)
                except Exception as e:
                    logger.error(str(e))

                if not project.model_path:
                    # Retrieve conversion data from cstracking db.
                    cs_id = project.cs_id
                    gid_pattern = project.gid_pattern
                    aid_pattern = project.aid_pattern
                    attribution_window = project.attribution_window
                    unique_by = project.unique_by

                    conversions = cs_get_conversions(
                        cs_id, gid_pattern, aid_pattern, dt_local,
                        dt_local + timedelta(days=1), attribution_window,
                        unique_by)
                else:
                    # Retrieve conversion data from fbapp signup table.
                    conversions = project.app_model.objects \
                        .daily_conversion(dt_local,
                                          project.queryset_filters_dict)

                DailyAdStats.objects.create(
                    project=project,
                    date=date_str,
                    impressions=adcampaign_stats['impressions'],
                    clicks=adcampaign_stats['clicks'],
                    link_clicks=adcampaign_stats['link_clicks'],
                    spent=adcampaign_stats['spent'],
                    conversions=conversions)

        project_set = Project.objects.filter(client_id=client_id,
                                             cs_daily_sync_required=True)
        for project in project_set:
            if project.network == 'LN':
                cs_id = project.cs_id
                gid_pattern = project.gid_pattern
                aid_pattern = project.aid_pattern
                attribution_window = project.attribution_window
                unique_by = project.unique_by

                conversions = cs_get_conversions(
                    cs_id, gid_pattern, aid_pattern, dt_local,
                    dt_local + timedelta(days=1), attribution_window,
                    unique_by)
                DailyAdStats.objects.create(
                    project=project,
                    date=date_str,
                    impressions=0,
                    clicks=0,
                    link_clicks=0,
                    spent=8,  # To remark this dailyadstats is to be completed
                    conversions=conversions)
