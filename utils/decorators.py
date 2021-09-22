from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator
# from https://www.bedjango.com/blog/top-6-django-decorators/


def group_required(*group_names):
   """Requires user membership in at least one of the groups passed in."""

   def in_groups(u):
       if u.is_authenticated():
           if bool(u.groups.filter(name__in=group_names)) | u.is_superuser:
               return True
       return False
   return user_passes_test(in_groups)


# The way to use this decorator is:
# @group_required(‘admins’, ‘seller’)
# def my_view(request, pk)

def superuser_only(function):
    """Limit view to superusers only."""

    def _inner(request, *args, **kwargs):
       if not request.user.is_superuser:
           raise PermissionDenied
       return function(request, *args, **kwargs)
    return _inner


# The way to use this decorator is:
# @superuser_only
# def my_view(request):

# in case of class based views
#  refer to https: // docs.djangoproject.com/en/3.2/topics/class-based-views/intro/
# @method_decorator(login_required, name='dispatch')
# class ProtectedView(TemplateView):

# decorators = [never_cache, login_required]


# @method_decorator(decorators, name='dispatch')
