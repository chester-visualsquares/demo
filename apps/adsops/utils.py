from datetime import date, timedelta

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum

from dashboard.models import AdStats, DailyAdStats, WeeklyAdStats
from dashboard.utils import facebook_campaign_stats


def project_stats(project, last_dailyadstats, allow_cache):
    if project.network == 'FB':
        try:
            adcampaign = project.adcampaign
        except ObjectDoesNotExist:
            return None

        project_api_adstats = facebook_campaign_stats(
            adcampaign,
            project.adcampaignsettings.start_date.strftime('%Y-%m-%d'),
            date.today().strftime('%Y-%m-%d'),
            allow_cache
        )

        status = project_api_adstats['status']
        spend_cap = (float(project_api_adstats['spend_cap']) / 100
                     if project_api_adstats['spend_cap'] else 'N/A')
        website_ctr = project_api_adstats['website_ctr']
        live_total_spent = project_api_adstats['spent'] / 100
        live_remain_spent = (project.adcampaignsettings.budget -
                             live_total_spent)
        link_clicks = float(project_api_adstats['link_clicks'])
        cplc = (live_total_spent / link_clicks
                if link_clicks else None)
    else:
        status = 'N/A'
        spend_cap = 'N/A'
        website_ctr = None
        live_total_spent = None
        live_remain_spent = None
        link_clicks = None
        cplc = None

    project_adstats_dict = project.dailyadstats_set.aggregate(
        impressions=Sum('impressions'),
        clicks=Sum('clicks'),
        link_clicks=Sum('link_clicks'),
        spent=Sum('spent'),
        conversions=Sum('conversions')
    )
    project_adstats = AdStats(
        project=project,
        impressions=project_adstats_dict['impressions'] or 0,
        spent=project_adstats_dict['spent'] or 0,
        clicks=project_adstats_dict['clicks'] or 0,
        link_clicks=link_clicks or project_adstats_dict['link_clicks'],
        conversions=project_adstats_dict['conversions'] or 0
    )

    remain_days = (project.adcampaignsettings.end_date - date.today() +
                   timedelta(days=1)).days
    remain_dollar_spent = (project.adcampaignsettings.budget -
                           project_adstats.dollar_spent)
    daily_spending_goal = (remain_dollar_spent / remain_days
                           if remain_days > 0 else None)

    if daily_spending_goal:
        if not last_dailyadstats.spent:
            daily_spending_class = 'spending-40-off'
        else:
            percent_diff = (
                abs(daily_spending_goal * 100 -
                    last_dailyadstats.spent) /
                daily_spending_goal)
            if percent_diff < 20:
                daily_spending_class = 'spending-on-track'
            elif 20 <= percent_diff < 40:
                daily_spending_class = 'spending-20-off'
            else:
                daily_spending_class = 'spending-40-off'
    else:
        daily_spending_class = 'spending-na'

    return ({'status': status,
             'spend_cap': spend_cap,
             'live_total_spent': live_total_spent,
             'remain_days': remain_days,
             'live_remain_spent': live_remain_spent,
             'remain_dollar_spent': remain_dollar_spent,
             'daily_spending_goal': daily_spending_goal,
             'daily_spending_class': daily_spending_class,
             'website_ctr': website_ctr,
             'cplc': cplc,
             },
            project_adstats)


def dailyadstats_set(project, start_date, days):
    project_dailyadstats_set = []
    dailyadstats_set = project.dailyadstats_set.filter(
        date__gte=start_date).order_by('date')
    for day in (start_date + timedelta(n) for n in range(days)):
        dailyadstats = dailyadstats_set.filter(date=day)
        if dailyadstats.exists():
            dailyadstats = dailyadstats.get()
        else:
            dailyadstats = DailyAdStats(
                project=project,
                date=day,
                impressions=None,
                clicks=None,
                link_clicks=None,
                spent=None,
                conversions=None)

        project_dailyadstats_set.append(dailyadstats)
    return project_dailyadstats_set


def weekly_adstats(project, start_date):
    dailyadstats_set = project.dailyadstats_set.filter(
        date__range=[start_date, start_date + timedelta(days=6)])

    weekly_adstats = dailyadstats_set.aggregate(
        impressions=Sum('impressions'),
        spent=Sum('spent'),
        clicks=Sum('clicks'),
        link_clicks=Sum('link_clicks'),
        conversions=Sum('conversions')
    )

    return WeeklyAdStats(
        project=project,
        start_date=start_date,
        impressions=weekly_adstats['impressions'] or 0,
        spent=weekly_adstats['spent'] or 0,
        clicks=weekly_adstats['clicks'] or 0,
        link_clicks=weekly_adstats['link_clicks'] or 0,
        conversions=weekly_adstats['conversions'] or 0
    )
