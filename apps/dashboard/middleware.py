from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
import pytz


class TimezoneMiddleware(object):
    def process_request(self, request):
        if request.user.is_anonymous():
            timezone.deactivate()
            return

        try:
            tzname = request.user.profile.timezone
            timezone.activate(pytz.timezone(tzname))
        except ObjectDoesNotExist:
                timezone.deactivate()
                print 'TIMEZONE DISABLED - '
                'No dashboard.models.UserProfile for this user'
