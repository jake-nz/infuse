from django.conf.urls.defaults import patterns, include, url
from django.conf import settings
#from django.contrib import admin
#admin.autodiscover()

urlpatterns = patterns('',
    #url(r'^admin/', include(admin.site.urls)),

    # pass all else on to website appcd SystemError
    url(r'', include(settings.PROJECT+'.website.urls')),
)
