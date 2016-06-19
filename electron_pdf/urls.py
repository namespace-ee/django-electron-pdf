# coding: utf-8

from django.conf.urls import url
from electron_pdf.views import PDFTemplateView

urlpatterns = [
    url(r'^test/$', PDFTemplateView.as_view(
        template_name='test.html',
        filename='test.pdf',
        show_content_in_browser=True,
        get_context_data=lambda: {'company_name': 'Namespace OÜ'},
    ), name='pdf'),
]
