# coding: utf-8

import re
import subprocess
import uuid
from tempfile import NamedTemporaryFile

try:
    from urllib.request import pathname2url
    from urllib.parse import urljoin
except ImportError:  # Python2
    from urllib import pathname2url
    from urlparse import urljoin

import django
from django.conf import settings
from django.core.files import File
from django.template import Context, RequestContext
from django.utils import six
from django.utils.encoding import smart_text


def electron_pdf(input, output_file=None, **kwargs):
    """
    Converts html to PDF using https://github.com/fraserxu/electron-pdf.
    input: input file or url of the html to be converted.
    output_file: Optional output file path. If None, the output is returned.
    **kwargs: Passed to electron-pdf via options

    example usage:
        electron_pdf(
            input='/tmp/example.html',
            landscape=True,
            printBackground=True,
            pageSize='A4'
        )
    """
    # Default options:
    options = getattr(settings, 'ELECTRON_PDF_OPTIONS', {})

    if not output_file:
        output_file = '/tmp/{}.pdf'.format(uuid.uuid4())

    subprocess.call('electron-pdf {} {}'.format(input.filename, output_file), shell=True)

    with open(output_file, 'r') as f:
        return File(f).read()


class RenderedFile(object):
    """
    Create a temporary file resource of the rendered template with context.
    The filename will be used for later conversion to PDF.
    """
    temporary_file = None
    filename = ''

    def __init__(self, template, context, request=None):
        self.temporary_file = render_to_temporary_file(
            template=template,
            context=context,
            request=request,
            prefix='electron_pdf', suffix='.html',
            delete=(not settings.ELECTRON_PDF_DEBUG)
        )
        self.filename = self.temporary_file.name

    def __del__(self):
        # Always close the temporary_file on object destruction.
        if self.temporary_file is not None:
            self.temporary_file.close()


def render_pdf_from_template(input_template, context, request=None, cmd_options={}):
    input_file = RenderedFile(
        template=input_template,
        context=context,
        request=request
    )
    return electron_pdf(input_file, **cmd_options)


def content_disposition_filename(filename):
    """
    Sanitize a file name to be used in the Content-Disposition HTTP
    header.
    Even if the standard is quite permissive in terms of
    characters, there are a lot of edge cases that are not supported by
    different browsers.
    See http://greenbytes.de/tech/tc2231/#attmultinstances for more details.
    """
    filename = filename.replace(';', '').replace('"', '')
    return http_quote(filename)


def http_quote(string):
    """
    Given a unicode string, will do its dandiest to give you back a
    valid ascii charset string you can use in, say, http headers and the
    like.
    """
    if isinstance(string, six.text_type):
        try:
            import unidecode
        except ImportError:
            pass
        else:
            string = unidecode.unidecode(string)
        string = string.encode('ascii', 'replace')
    # Wrap in double-quotes for ; , and the like
    string = string.replace(b'\\', b'\\\\').replace(b'"', b'\\"')
    return '"{0!s}"'.format(string.decode())


def pathname2fileurl(pathname):
    """Returns a file:// URL for pathname. Handles OS-specific conversions."""
    return urljoin('file:', pathname2url(pathname))


def make_absolute_paths(content):
    """Convert all MEDIA files into a file://URL paths in order to
    correctly get it displayed in PDFs."""
    overrides = [{
        'root': settings.MEDIA_ROOT,
        'url': settings.MEDIA_URL,
    }, {
        'root': settings.STATIC_ROOT,
        'url': settings.STATIC_URL,
    }]
    has_scheme = re.compile(r'^[^:/]+://')

    for x in overrides:
        if not x['url'] or has_scheme.match(x['url']):
            continue

        if not x['root'].endswith('/'):
            x['root'] += '/'

        occur_pattern = '''["|']({0}.*?)["|']'''
        occurences = re.findall(occur_pattern.format(x['url']), content)
        occurences = list(set(occurences))  # Remove dups
        for occur in occurences:
            content = content.replace(
                occur,
                pathname2fileurl(x['root']) + occur[len(x['url']):]
            )

    return content


def render_to_temporary_file(template, context, request=None, mode='w+b',
                             bufsize=-1, suffix='.html', prefix='tmp',
                             dir=None, delete=True):
    if django.VERSION < (1, 8):
        # If using a version of Django prior to 1.8, ensure ``context`` is an
        # instance of ``Context``
        if not isinstance(context, Context):
            if request:
                context = RequestContext(request, context)
            else:
                context = Context(context)
        content = template.render(context)
    else:
        content = template.render(context, request)

    content = smart_text(content)
    content = make_absolute_paths(content)

    try:
        # Python3 has 'buffering' arg instead of 'bufsize'
        tempfile = NamedTemporaryFile(
            mode=mode,
            buffering=bufsize,
            suffix=suffix,
            prefix=prefix,
            dir=dir,
            delete=delete
        )
    except TypeError:
        tempfile = NamedTemporaryFile(
            mode=mode,
            bufsize=bufsize,
            suffix=suffix,
            prefix=prefix,
            dir=dir,
            delete=delete
        )

    try:
        tempfile.write(content.encode('utf-8'))
        tempfile.flush()
        return tempfile
    except:
        # Clean-up tempfile if an Exception is raised.
        tempfile.close()
        raise
