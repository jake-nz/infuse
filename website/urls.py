from django.conf.urls.defaults import patterns, include, url
from django.views.generic import TemplateView, RedirectView

# renders template from parh given in params
class DefaultView(TemplateView):
    def get_template_names(self):
        return [self.kwargs['path'], self.kwargs['path']+'.html']            


urlpatterns = patterns('',
    # / -> index.html
    (r'^$', TemplateView.as_view(template_name="index.html")),
    # /anything -> anything.html
    (r'^(?P<path>[\w\-]+)$', DefaultView.as_view()),

)

# redirects for old site
#urlpatterns += patterns('',
#    #(r'^old url with no start slash$', RedirectView.as_view(url="new url with start slash")),
#    (r'^no/slash/page/on/old_site.html$', RedirectView.as_view(url="/slash/new/url/")),
#)