from fabric.api import *

# globals
env.project_name = 'template'
env.domain = 'template.co.nz'

# environments
def production():
    env.hosts = ['clients.infusecreative.co.nz']
    env.path = 'var/www/'+env.domain
    env.user = 'deploy'
    env.git_branch = env.project_name
    env.apache_conf = apache_conf % env
    env.wsgi_conf = wsgi_conf % env

def dev():
    production()
    env.domain = 'dev.'+env.domain
    env.path += '/dev'
    env.apache_conf = apache_conf % env
    env.wsgi_conf = wsgi_conf % env

environments = [production, dev]

# tasks
#########

def test():
    "Run the test suite and bail out if it fails"
    local("python manage.py test", fail="abort")

def setup():
    """
    Setup directories, a fresh virtualenv, configuration, get code from github
    """
    require('project_name')
    require('domain')
    
    # mkdirs
    run('mkdir -p %(path)s/{httpdocs,subdomains,log,django/%(project_name)s,virtualenv};' % env)
    # get code
    run('git clone --depth 1 --branch %(git_branch)s git://github.com/jakecr/infuse.git %(path)s/django/%(project_name)s' % env)
    # create virtualenv
    run('cd %(path)s/virtualenv; virtualenv --no-site-packages .' % env)

    install_requirements()
    configure()

def install_requirements():
    """
    install requirements
    """
    require('project_name')
    require('domain')
    
    run('pip install -E %(path)s/virtualenv -r %(path)s/django/%(project_name)s/requirements.txt' % env)

def configure():
    """
    Create config files
    """
    sudo('echo "%(apache_conf)s" > /etc/apache2/sites-available/%(domain)s' % env)
    sudo('echo "%(wsgi_conf)s" > %(path)s/django/django.wsgi' % env)
    sudo("a2ensite %(domain)s" % env)
    sudo("a2ensite %(domain)s" % env)
    sudo("a2ensite %(domain)s" % env)

def deploy():
    require('project_name')
    require('domain')
    
    # update code
    run('cd %(path)s/django/%(project_name)s; git pull' % env)
    # reload python files
    run('touch %(path)s/django/django.wsgi')

apache_conf = """
<VirtualHost *:80>
        # remove www
        ServerName www.%(domain)s
        RedirectPermanent / http://%(domain)s
</VirtualHost>

<VirtualHost *:80>
        ServerName %(domain)s

        Alias /static %(path)s/django/%(project_name)s/static/
        Alias /favicon.ico %(path)s/django/%(project_name)s/static/favicon.ico
        WSGIScriptAlias / %(path)s/django/django.wsgi

        DocumentRoot /var/www/%(domain)s/httpdocs
        <Directory /var/www/%(domain)s/httpdocs/>
                Options -Indexes -MultiViews
                Options FollowSymLinks
                AllowOverride Options
                Order allow,deny
                allow from all
        </Directory>

        ErrorLog /var/www/%(domain)s/log/error.log
        LogLevel warn
        CustomLog /var/www/%(domain)s/log/access.log "%{%d:%m:%Y %H:%M:%S}t %h %m:http://%{Host}i%U%q %>s %b \"%{User-Agent}i\""

        # custom 404 page
        #ErrorDocument 404 /404.html
        
        # We don't need to tell everyone we're apache.
        ServerSignature Off

        # Force the latest IE version, in various cases when it may fall back to IE7 mode
        #  github.com/rails/rails/commit/123eb25#commitcomment-118920
        # Use ChromeFrame if it's installed for a better experience for the poor IE folk
        <IfModule mod_setenvif.c>
          <IfModule mod_headers.c>
            BrowserMatch MSIE ie
            Header set X-UA-Compatible "IE=Edge,chrome=1" env=ie
          </IfModule>
        </IfModule>
</VirtualHost>
"""

wsgi_conf = """
import os, sys

# put the Django project on sys.path
sys.path.insert(0, (os.path.abspath(os.path.dirname(__file__))))

os.environ['DJANGO_SETTINGS_MODULE'] = '%(project_name)s.settings'
#os.environ['PYTHON_EGG_CACHE'] = '/usr/lib/python2.4/eggcache'
from django.core.handlers.wsgi import WSGIHandler
application = WSGIHandler()
"""