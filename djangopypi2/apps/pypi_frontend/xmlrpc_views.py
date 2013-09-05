import xmlrpclib
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseNotAllowed, HttpResponse
from ..pypi_packages.models import Package
from ..pypi_packages.models import Release

def is_xmlrpc_request(request):
    return (request.method == 'POST') and (request.META['CONTENT_TYPE'] == 'text/xml')

class XMLRPCResponse(HttpResponse):
    """ A wrapper around the base HttpResponse that dumps the output for xmlrpc
    use """
    def __init__(self, params=(), methodresponse=True, *args, **kwargs):
        super(XMLRPCResponse, self).__init__(xmlrpclib.dumps(params,
                                                             methodresponse=methodresponse),
                                            content_type='text/xml',
                                             *args, **kwargs)

def handle_xmlrpc_request(request):
    """
    Parse the request and dispatch to the appropriate view
    """
    args, command = xmlrpclib.loads(request.raw_post_data)

    if command in XMLRPC_COMMANDS:
        return XMLRPC_COMMANDS[command](request, *args)
    else:
        return HttpResponseNotAllowed(XMLRPC_COMMANDS.keys())

def list_packages(request):
    return XMLRPCResponse(params=(list(Package.objects.values_list('name', flat=True).order_by('name').all()),),)

def package_releases(request, package_name, show_hidden=False):
    try:
        return XMLRPCResponse(params=(list(Package.objects.get(name=package_name).releases.filter(hidden=show_hidden).values_list('version', flat=True)),))
    except Package.DoesNotExist:
        return XMLRPCResponse(params=([],))

def release_urls(request, package_name, version):
    base_url = '%s://%s' % (request.is_secure() and 'https' or 'http',
                              request.get_host())
    dists = []
    try:
        for dist in Package.objects.get(name=package_name).releases.get(version=version).distributions.all():
            dists.append({
                'url': '%s%s' % (base_url, dist.get_absolute_url()),
                'packagetype': dist.filetype,
                'filename': dist.filename,
                'size': dist.content.size,
                'md5_digest': dist.md5_digest,
                'downloads': 0,
                'has_sig': len(dist.signature)>0,
                'python_version': dist.pyversion,
                'comment_text': dist.comment
            })
    except (Package.DoesNotExist, Release.DoesNotExist):
        pass

    return XMLRPCResponse(params=(dists,))

def release_data(request, package_name, version):
    output = {
        'name': '',
        'version': '',
        'stable_version': '',
        'author': '',
        'author_email': '',
        'maintainer': '',
        'maintainer_email': '',
        'home_page': '',
        'license': '',
        'summary': '',
        'description': '',
        'keywords': '',
        'platform': '',
        'download_url': '',
        'classifiers': '',
        'requires': '',
        'requires_dist': '',
        'provides': '',
        'provides_dist': '',
        'requires_external': '',
        'requires_python': '',
        'obsoletes': '',
        'obsoletes_dist': '',
        'project_url': '',
    }
    try:
        release = Package.objects.get(name=package_name).releases.get(version=version)
        output.update({'name': package_name, 'version': version,})
        output.update(release.package_info)
    except (Package.DoesNotExist, Release.DoesNotExist):
        pass

    return XMLRPCResponse(params=(output,))

def search(request, spec, operator='or'):
    """
    search(spec[, operator])

    Search the package database using the indicated search spec.
    The spec may include any of the keywords described in the above list (except 'stable_version' and 'classifiers'), for example: {'description': 'spam'} will search description fields. Within the spec, a field's value can be a string or a list of strings (the values within the list are combined with an OR), for example: {'name': ['foo', 'bar']}. Valid keys for the spec dict are listed here. Invalid keys are ignored:
    name
    version
    author
    author_email
    maintainer
    maintainer_email
    home_page
    license
    summary
    description
    keywords
    platform
    download_url
    Arguments for different fields are combined using either "and" (the default) or "or". Example: search({'name': 'foo', 'description': 'bar'}, 'or'). The results are returned as a list of dicts {'name': package name, 'version': package release version, 'summary': package release summary}
    """

    # Note: The implementation below is just enough to make "pip search" works.
    # It is not the full implementation of PyPI XMLRPC API
    name = spec['name'] if 'name' in spec else ''
    summary = spec['summary'] if 'summary' in spec else ''

    results = Release.simple_search(name, summary)
    response = []
    for result in results:
        result_summary = result.package_info['summary'] if 'summary' in result.package_info else ''
        output = {
            'name': result.package.name,
            'version': result.version,
            'summary': result_summary,
        }
        response.append(output)
    return XMLRPCResponse(params=(response,))

def changelog(since):
    """
    changelog(since)

    Retrieve a list of four-tuples (name, version, timestamp, action) since the given timestamp. All timestamps are UTC values. The argument is a UTC integer seconds since the epoch.
    """

    output = {
        'name': '',
        'version': '',
        'timestamp': '',
        'action': '',
    }
    return XMLRPCResponse(params=(output,))

def ratings(request, name, version, since):
    return XMLRPCResponse(params=([],))

def docs(request, package_name):
    response = ''
    try:
        release = Package.objects.get(name=package_name).latest
        response = release.package_info['description']
    except ObjectDoesNotExist:
        response = 'Package with name %s not found.' % package_name
    return XMLRPCResponse(params=(response,))

def info(request, package_name, package_version = -1):
    output = {
        'name': '',
        'version': '',
        'summary': '',
        'author': '',
        'home_page': '',
        'project_page': ''
    }
    release = None
    if package_version == -1:
        try:
            release = Package.objects.get(name=package_name).latest
        except ObjectDoesNotExist:
            pass
    else:
        try:
            release = Package.objects.get(name=package_name).releases.get(version=package_version)
        except ObjectDoesNotExist:
            pass

    if release is not None:
        output["name"] = package_name
        output["version"] = release.version
        for key, value in release.package_info.items():
            if key in output:
                output[key] = value
        output["project_page"] = request.build_absolute_uri(release.get_absolute_url())
    return XMLRPCResponse(params=(output,))

XMLRPC_COMMANDS = {
    'list_packages': list_packages,
    'package_releases': package_releases,
    'release_urls': release_urls,
    'release_data': release_data,
    'search': search,
    #'changelog': changelog, Not done yet
    #'ratings': ratings, Not done yet

    # Non-standard:
    'docs': docs,
    'info': info,
}
