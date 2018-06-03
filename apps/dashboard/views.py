import csv
import json
import urllib
import urllib2

from datetime import date, timedelta
from decimal import Decimal
from requests.exceptions import Timeout

from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.utils.encoding import smart_str
from django.views.decorators.http import require_http_methods

from dashboard.decorators import client_required, project_required
from dashboard.forms import ChannelForm
from dashboard.models import Channel, Project
from dashboard.templatetags.dashboard_extras import (country_name,
                                                     humanize_boolean)
from dashboard.utils import encode_utf8, localtime
from pyshorteners import Shortener


@require_http_methods(['GET'])
@login_required
@client_required
@project_required
def country_breakdown(request, project_id,
                      template_name='dashboard/country_breakdown.html'):
    project = request.project
    signup_breakdown = getattr(project.app_model.objects, 'signup_breakdown',
                               None)

    if signup_breakdown:
        signup_breakdown = signup_breakdown(
            project.queryset_filters_dict)

    return render(request, template_name, {
        'countrystats_set': project.countrystats_set,
        'project': project,
        'signup_breakdown': signup_breakdown,
    })


@require_http_methods(['GET'])
@login_required
@client_required
@project_required
def download_report(request, project_id, report_type, network=None):
    project = request.project

    allowed_types = ('channel-list', 'daily-report',
                     'country-breakdown', 'signup-list')
    if report_type not in allowed_types:
        raise Http404

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = ('attachment; filename=%s.csv'
                                       % report_type)

    writer = csv.writer(response, csv.excel)
    response.write(u'\ufeff'.encode('utf8'))
    if report_type == 'daily-report':
        dailyadstats_set = project.dailyadstats_set.order_by('date')

        writer.writerow([
            smart_str(u"Date"),
            smart_str(u"Impressions"),
            smart_str(u"Spending"),
            smart_str(u"Link Clicks"),
            smart_str(u"# of Registrations"),
            smart_str(u"CPA"),
        ])

        _two_places = lambda x: Decimal(x).quantize(Decimal('0.01'))
        for adstats in dailyadstats_set:
            writer.writerow([
                smart_str(adstats.date),
                smart_str(adstats.impressions),
                smart_str(_two_places(adstats.dollar_spent)),
                smart_str(adstats.clicks),
                smart_str(adstats.conversions),
                smart_str(_two_places(adstats.dollar_cpa)
                          if adstats.dollar_cpa else 'N/A'),
            ])

    elif report_type == 'country-breakdown':
        countrystats_set = project.countrystats_set

        writer.writerow([
            smart_str(project.country_field_name.title()),
            smart_str(u"# of Reg"),
        ])

        for countrystats in countrystats_set:
            writer.writerow([
                smart_str(country_name(
                    countrystats[project.country_field_name])),
                smart_str(countrystats['count']),
            ])

    elif report_type == 'signup-list':
        allowed_networks = ('facebook', 'linkedin', 'wechat', 'twitter')
        if network not in allowed_networks:
            raise Http404

        report_fields = project.app_model.objects.report_fields()
        signup_report = project.app_model.objects.signup_report(
            network,
            project.queryset_filters_dict,
            project.channel_set.all())

        writer = csv.DictWriter(response, fieldnames=report_fields)
        writer.writeheader()

        for signup in signup_report:
            signup = {k: encode_utf8(localtime(humanize_boolean(v)))
                      for k, v in signup.iteritems()}
            writer.writerow(signup)

    elif report_type == 'channel-list':
        channel_report_fields = project.app_model.objects \
            .channel_report_fields()
        channel_report = project.app_model.objects.channel_report(
            project.channel_set.all())

        writer = csv.DictWriter(response, fieldnames=channel_report_fields)
        writer.writeheader()

        for channel in channel_report:
            channel = {k: encode_utf8(v)
                       for k, v in channel.iteritems()}
            writer.writerow(channel)

    return response


@require_http_methods(['GET'])
@login_required
@client_required
@project_required
def daily_report(request, project_id,
                 template_name='dashboard/daily_report.html'):
    project = request.project
    dailyadstats_set = project.dailyadstats_set.order_by('date')

    adstats = dailyadstats_set.aggregate(
        impressions=Sum('impressions'),
        spent=Sum('spent'),
        clicks=Sum('clicks'),
        conversions=Sum('conversions')
    )

    adstats['impressions'] = adstats['impressions'] or 0
    adstats['dollar_spent'] = float(adstats['spent'] or 0) / 100
    adstats['clicks'] = adstats['clicks'] or 0
    adstats['conversions'] = adstats['conversions'] or 0

    if adstats['conversions'] == 0:
        adstats['dollar_cpa'] = None
    else:
        adstats['dollar_cpa'] = (adstats['dollar_spent'] /
                                 float(adstats['conversions']))

    return render(request, template_name, {
        'adstats': adstats,
        'dailyadstats_set': dailyadstats_set,
        'project': project,
    })


@require_http_methods(['GET'])
@login_required
@client_required
def projects(request, template_name='dashboard/projects.html'):
    dashboard_end_date = date.today() - timedelta(days=360)
    projects = Project.objects.filter(
        client=request.client,
        adcampaignsettings__end_date__gte=dashboard_end_date,
        is_active=True).order_by('-last_update')

    return render(request, template_name, {
        'client': request.client,
        'projects': projects,
    })


@require_http_methods(['GET'])
@login_required
@client_required
@project_required
def signup_list(request, network, project_id,
                template_name='dashboard/signup_list.html'):
    project = request.project
    allowed_networks = ('facebook', 'linkedin', 'wechat', 'twitter')
    if network not in allowed_networks:
        raise Http404

    signup_breakdown = getattr(project.app_model.objects, 'signup_breakdown',
                               None)

    if signup_breakdown:
        signup_breakdown = signup_breakdown(
            project.queryset_filters_dict,
            network)

    return render(request, template_name, {
        'network': network,
        'project': project,
        'report_fields': project.app_model.objects.report_fields,
        'signup_breakdown': signup_breakdown,
        'signup_report': project.app_model.objects.signup_report(
            network, project.queryset_filters_dict, project.channel_set.all()),
    })


@require_http_methods(['GET', 'POST'])
@login_required(login_url='/dashboard/login')
@client_required
def create_shorten_links(request,
                         template_name='dashboard/create_shorten_links.html'):
    if request.method == 'GET':
        form = ChannelForm(client=request.client)
        return render(request, template_name, {
            'form': form
        })
    elif request.method == 'POST':
        form = ChannelForm(data=request.POST, client=request.client)
        if form.is_valid():
            channel = form.save(commit=False)

            if form.cleaned_data['platform'] != 'WEC':
                channel.network = 'FB'
                aid_prefix = 'FBCS'
                aid_2 = channel.project.aid_pattern[4:6]
                project = Project.objects.get(name=channel.project)
                if form.cleaned_data['platform'] == 'FBC':
                    url_str = project.non_cn_url_chi
                    channel.language = 'CHI'
                    aid_offset = 1000
                else:
                    url_str = project.non_cn_url_eng
                    channel.language = 'ENG'
                    aid_offset = 0

                aid_3 = Channel.objects.filter(
                    project=channel.project, network='FB',
                    language=channel.language
                ).count() + 8001 + aid_offset
                channel.aid = str(aid_prefix) + str(aid_2) + str(aid_3)
                query_dict = {'fbcsid': channel.aid,
                              'lang': channel.language.lower()}
                query_string = urllib.urlencode(query_dict)
                long_url = '%s?%s' % (url_str, query_string)

                shortener = Shortener(
                    'Google', api_key=settings.DASHBOARD_GOOGLE_API_KEY)
                for i in xrange(3):
                    try:
                        channel.short_url = shortener.short(long_url)
                    except Timeout as e:
                        last_err = e
                    else:
                        break
                else:
                    raise Exception(
                        'Failed to generate the Google shorten link, %s'
                        % (str(last_err))
                    )

            elif form.cleaned_data['platform'] == 'WEC':
                aid_1 = 'WECS'
                aid_2 = channel.project.aid_pattern[4:6]
                channel.network = 'WE'
                channel.language = 'SC'
                url_str = Project.objects.get(name=channel.project).cn_url
                aid_3 = Channel.objects.filter(project=channel.project,
                                               network='WE').count() + 9001
                channel.aid = str(aid_1) + str(aid_2) + str(aid_3)
                long_url = '%s?fbcsid=%s' % (url_str, channel.aid)
                service = settings.DASHBOARD_WEIBO_API_KEY
                for i in xrange(3):
                    try:
                        channel.short_url = json.loads(getLink(
                            service, long_url))[0].get('url_short', 'None')
                    except Timeout as e:
                        last_err = e
                    else:
                        break
                else:
                    raise Exception(
                        'Failed to generate the Tencent shorten link, %s'
                        % (str(last_err))
                    )
            channel.save()

            return render(request,
                          'dashboard/create_shorten_links_finish.html',
                          {'channel': channel, })
        else:
            return render(request, template_name, {
                'form': form,
            })


@require_http_methods(['GET'])
@login_required
@client_required
@project_required
def channel_list(request, project_id,
                 template_name='dashboard/channel_list.html'):
    project = request.project

    return render(request, template_name, {
        'channel_report': project.app_model.objects.channel_report(
            project.channel_set.all()),
        'channel_report_fields':
            project.app_model.objects.channel_report_fields,
        'project': project,
    })


def getLink(service, url):
    terms = urllib.quote_plus(url.strip())
    url = service + terms
    data = urllib2.urlopen(url).read()
    return data
