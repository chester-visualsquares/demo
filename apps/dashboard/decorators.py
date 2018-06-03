from django.http import Http404
from django.shortcuts import get_object_or_404

from dashboard.models import Project


def client_required(func):
    def wrapped(request, *args, **kwargs):
        profile = request.user.profile

        if not profile.client:
            raise Http404
        request.client = profile.client
        return func(request, *args, **kwargs)
    return wrapped


def project_required(func):
    def wrapped(request, *args, **kwargs):
        project = get_object_or_404(Project,
                                    pk=kwargs['project_id'],
                                    client=request.client)
        request.project = project
        return func(request, *args, **kwargs)
    return wrapped
