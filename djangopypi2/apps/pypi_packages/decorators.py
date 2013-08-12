from django.contrib.auth import login, REDIRECT_FIELD_NAME
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.utils.http import urlquote

try:
    from functools import wraps, WRAPPER_ASSIGNMENTS
except ImportError:
    from django.utils.functional import wraps, WRAPPER_ASSIGNMENTS

try:
    from django.utils.decorators import available_attrs
except ImportError:
    def available_attrs(fn):
        return tuple(a for a in WRAPPER_ASSIGNMENTS if hasattr(fn, a))

def user_owns_package(login_url=None, redirect_field_name=REDIRECT_FIELD_NAME):
    """
    Decorator for views that checks whether the user owns the currently requested
    package.
    """
    if not login_url:
        from django.conf import settings
        login_url = settings.LOGIN_URL
    
    def decorator(view_func):
        def _wrapped_view(request, package_name, *args, **kwargs):
            if (request.user.is_authenticated() and
                request.user.packages_owned.filter(name=package_name).count() > 0):
                return view_func(request, package_name=package_name, *args, **kwargs)
            return HttpResponseForbidden()
        return wraps(view_func, assigned=available_attrs(view_func))(_wrapped_view)
    return decorator

def user_maintains_package(login_url=None, redirect_field_name=REDIRECT_FIELD_NAME):
    """
    Decorator for views that checks whether the user maintains (or owns) the
    currently requested package.
    """
    if not login_url:
        from django.conf import settings
        login_url = settings.LOGIN_URL

    def decorator(view_func):
        def _wrapped_view(request, package_name, *args, **kwargs):
            if (request.user.is_authenticated() and
                (request.user.packages_owned.filter(name=package_name).count() > 0 or
                request.user.packages_maintained.filter(name=package_name).count() > 0)):
                return view_func(request, package_name=package_name, *args, **kwargs)
            return HttpResponseForbidden()
        return wraps(view_func, assigned=available_attrs(view_func))(_wrapped_view)
    return decorator
