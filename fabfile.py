from fabric.api import *
from StringIO import StringIO

# globals
env.project_name = 'template'
env.domain = 'template.co.nz'

# environments
def production():
    env.hosts = ['clients.infusecreative.co.nz']
    env.path = '/var/www/'+env.domain
    env.user = 'ubuntu'
    env.git_branch = env.project_name
    env.apache_conf = apache_conf
    env.wsgi_conf = wsgi_conf

def dev():
    production()
    env.subdomain = 'dev'
    env.domain = env.subdomain+'.'+env.domain
    env.path += '/' + env.subdomain
    env.apache_conf = apache_conf
    env.wsgi_conf = wsgi_conf

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
    sudo('mkdir -m 755 -p %(path)s' % env)
    sudo('chown ubuntu:ubuntu %(path)s' % env)
    run('mkdir -m 755 -p %(path)s/{httpdocs,subdomains,log,django/%(project_name)s,virtualenv}' % env)
    # get code
    run('git clone --depth 1 --branch %(git_branch)s git://github.com/jakecr/infuse.git %(path)s/django/%(project_name)s' % env)
    # create virtualenv
    run('virtualenv --no-site-packages %(path)s/virtualenv' % env)

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
    put(StringIO(env.apache_conf.format(**env)), '/etc/apache2/sites-available/%(domain)s' % env, use_sudo=True)
    put(StringIO(env.wsgi_conf.format(**env)), '%(path)s/django/django.wsgi' % env)
    sudo("a2ensite %(domain)s" % env)
    run("apache2ctl configtest" % env)
    sudo("apache2ctl graceful" % env)

def rollback():
    require('project_name')
    require('domain')
    
    # update code
    with cd('%(path)s/django/%(project_name)s' % env): 
        run('git reset --hard ORIG_HEAD')
    # reload python files
    run('touch %(path)s/django/django.wsgi' % env)

def disable():
    """
    Create config files
    """
    sudo("a2dissite %(domain)s" % env)
    run("apache2ctl configtest" % env)
    sudo("apache2ctl graceful" % env)

def update():
    require('project_name')
    require('domain')
    
    # update code
    with cd('%(path)s/django/%(project_name)s' % env): 
        run('git pull' % env)
    # reload python files
    run('touch %(path)s/django/django.wsgi' % env)

apache_conf = """
<VirtualHost *:80>
        # remove www
        ServerName www.{domain}
        RedirectPermanent / http://{domain}
</VirtualHost>

<VirtualHost *:80>
        ServerName {domain}

        Alias /static {path}/django/{project_name}/static/
        Alias /favicon.ico {path}/django/{project_name}/static/favicon.ico
        WSGIScriptAlias / {path}/django/django.wsgi

        DocumentRoot {path}/httpdocs
        <Directory {path}/httpdocs/>
                Options -Indexes -MultiViews
                Options FollowSymLinks
                AllowOverride Options
                Order allow,deny
                allow from all
        </Directory>

        ErrorLog {path}/log/error.log
        LogLevel warn

        CustomLog {path}/log/access.log "%{{%d:%m:%Y %H:%M:%S}}t %h %m:http://%{{Host}}i%U%q %>s %b \\"%{{User-Agent}}i\\""

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

os.environ['DJANGO_SETTINGS_MODULE'] = '{project_name}.settings'
#os.environ['PYTHON_EGG_CACHE'] = '/usr/lib/python2.4/eggcache'
from django.core.handlers.wsgi import WSGIHandler
application = WSGIHandler()
"""