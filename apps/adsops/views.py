from datetime import date, timedelta

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from adsops.utils import dailyadstats_set, project_stats, weekly_adstats
from dashboard.models import Project


@require_http_methods(['GET'])
@login_required
@user_passes_test(lambda u: u.is_staff, login_url='/dashboard/login')
def performance_tracker(request,
                        template_name='adsops/performance_tracker.html'):
    project_list = []
    for project in Project.objects.filter(adcampaignsettings__isnull=False,
                                          adcampaignsettings__is_active=True
                                          ).order_by('client__name',
                                                     'last_update'):

        allow_cache = not request.GET.get('refresh', '0') == '1'

        # NOTE: date.today() returns the server's local date.
        start_date = date.today() - timedelta(days=10)
        project_dailyadstats_set = dailyadstats_set(project, start_date, 10)
        project_stats_result = project_stats(project,
                                             project_dailyadstats_set[-1],
                                             allow_cache)
        if not project_stats_result:
            continue

        offset = (date.today().weekday() - 6) % 7
        last_sunday = date.today() - timedelta(days=offset)

        weekly_adstats_set = []
        for sunday in (last_sunday - timedelta(days=7) * n for n
                       in reversed(range(0, 5))):
            weekly_adstats_set.append(weekly_adstats(project, sunday))

        current_week_adstats = weekly_adstats_set[-1]
        past_4_weeks_adstats_set = weekly_adstats_set[:4]

        project_list.append((
            project,
            project_stats_result[0],
            project_stats_result[1],
            project_dailyadstats_set,
            current_week_adstats,
            past_4_weeks_adstats_set,
        ))

    return render(request, template_name, {
        'project_list': project_list,
    })
