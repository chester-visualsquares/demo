from datetime import datetime, timedelta
import json
import os.path

from django.db import connections
from django.utils import timezone
from facebookads import FacebookAdsApi, FacebookSession
from facebookads.adobjects.adsinsights import AdsInsights
from facebookads.adobjects.campaign import Campaign
from facebookads.exceptions import FacebookError
import pytz
from facebook.constants import BUSINESS_APP_ID, BUSINESS_APP_SECRET


def cs_get_conversions(cs_id, gid_pattern, aid_pattern, start_dt, end_dt,
                       attribution_window=None, unique_by=None):
    start_dt_str = start_dt.astimezone(pytz.utc).strftime('%Y-%m-%d %H:%M')
    end_dt_str = end_dt.astimezone(pytz.utc).strftime('%Y-%m-%d %H:%M')

    cursor = connections['cstracking'].cursor()
    sql_unique_by = '''
    SELECT
        COUNT(%s)
    '''
    if unique_by:
        sql_unique_by = sql_unique_by % ('DISTINCT(' + unique_by + ')')
    else:
        sql_unique_by = sql_unique_by % '*'

    sql = sql_unique_by + '''
    FROM
        tracking_conversion t1,
        tracking_visit t2,
        tracking_visitor t3,
        tracking_visitorfootprint t4
    WHERE
        t1.visit_id = t2.id
    AND t4.visit_id = t2.id
    AND t2.visitor_id = t3.id
    AND account_id = %(cs_id)s
    AND t1.gid LIKE %(gid_pattern)s
    AND t1.aid LIKE %(aid_pattern)s
    AND t1.aid not LIKE '%%0000'
    AND t2.server_timestamp BETWEEN %(start_dt_str)s AND %(end_dt_str)s
    '''

    sql_attribution_window = '''
    AND DATEDIFF(t2.server_timestamp, (SELECT v.server_timestamp
    FROM
        tracking_click c,
        tracking_visit v,
        tracking_visitor t
    WHERE
        c.aid = t1.aid AND v.visitor_id = t.id
    AND t.id = t3.id
    AND c.visit_id = v.id
    AND v.server_timestamp < t2.server_timestamp
    ORDER BY v.server_timestamp DESC
    LIMIT 1)) <= %(attribution_window)s
    '''
    if attribution_window:
        sql += sql_attribution_window

    sql_context = locals()
    cursor.execute(sql, sql_context)
    return cursor.fetchall()[0][0]


def encode_utf8(value):
    if isinstance(value, unicode):
        return value.encode('utf8')
    else:
        return value


def facebook_campaign_stats(adcampaign, start_date_str, end_date_str,
                            allow_cache=False):
    session = FacebookSession(
        BUSINESS_APP_ID,
        BUSINESS_APP_SECRET,
        adcampaign.ad_account.access_token
    )
    api = FacebookAdsApi(session)
    FacebookAdsApi.set_default_api(api)
    params = {
        'time_range': {
            'since': start_date_str,
            'until': end_date_str,
        },
        'fields': [
            AdsInsights.Field.impressions,
            AdsInsights.Field.clicks,
            AdsInsights.Field.spend,
            AdsInsights.Field.actions,
            AdsInsights.Field.ctr,
            AdsInsights.Field.inline_link_clicks,
            AdsInsights.Field.inline_link_click_ctr,
            AdsInsights.Field.cpc,
        ],
    }

    cache_file = '/tmp/%s-%s-%s.json' % (adcampaign.fbid, start_date_str,
                                         end_date_str)
    if allow_cache and os.path.isfile(cache_file):
        last_modified = datetime.fromtimestamp(
            os.path.getmtime(cache_file))
        if last_modified > datetime.now() - timedelta(hours=1):
            with open(cache_file, 'r') as cache_file:
                return json.load(cache_file)

    last_err = None

    # TODO(chesterwu): verify the API rate limit not exceeded. Ref -
    # developers.facebook.com/docs/marketing-api/api-rate-limiting
    for i in xrange(3):
        try:
            campaign = Campaign(adcampaign.fbid)
            campaign_api_response = campaign.remote_read(fields=[
                Campaign.Field.effective_status,
                Campaign.Field.spend_cap])
            insights = campaign.get_insights(params=params)
        except FacebookError as e:
            last_err = e
        else:
            break
    else:
        raise Exception(
            'Failed to retrieve Facebook data for Adcampaign %s: %s'
            % (adcampaign, str(last_err)))

    if insights:
        insight = insights[0]
        campaign_stats = {
            'status': campaign_api_response.get('effective_status'),
            'spend_cap': campaign_api_response.get('spend_cap'),
            'impressions': insight['impressions'],
            'clicks': insight['clicks'],
            'spent': float(insight['spend']) * 100,
            'ctr': insight['ctr'],
            'link_clicks': insight['inline_link_clicks'],
            'website_ctr': insight['inline_link_click_ctr'],
            'cpc': insight['cpc'],
        }
    else:
        campaign_stats = {
            'status': campaign_api_response.get('effective_status'),
            'spend_cap': campaign_api_response.get('spend_cap'),
            'impressions': 0,
            'clicks': 0,
            'link_clicks': 0,
            'spent': 0,
            'ctr': None,
            'website_ctr': None,
            'cpc': None,
        }

    with open(cache_file, 'w') as cache_file:
        json.dump(campaign_stats, cache_file)
    return campaign_stats


def localtime(value):
    if isinstance(value, datetime):
        return timezone.localtime(value)
    else:
        return value
