from fabric.api import *
from fabric.colors import red
from fabric.tasks import WrappedCallableTask
from StringIO import StringIO

# Edit these three
env.project = 'counsellingworx'
env.domain = 'counsellingworx.co.nz'
env.redirects = [] # optional. eg ['other.co.nz', 'template.com']

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

env.aliases = []
env.hosts = ['clients.infusecreative.co.nz']
env.path = '/var/www/'+env.domain
env.user = 'ubuntu'
env.git_branch = env.domain
# these 2 vars are big so set at end
# env.apache_conf
# env.wsgi_conf

class SubdomainTask(WrappedCallableTask):

    def run(self, *args, **kwargs):

        require('project')
        require('domain')
        require('path')

        if env.project == 'template' or env.domain == 'template.co.nz':
            print(red("You must set") + " project " + red("and") + " domain " + red("by editing fabfile.py!"))
            return

        if len(args):
            env.subdomain = args[0]
            env.domain = env.subdomain+'.'+env.domain
            env.path = env.path+'/subdomains/'+env.subdomain
            args = args[1:]
        else:
            env.subdomain = ''
        return self.wrapped(*args, **kwargs)

# tasks
#########

@task(task_class=SubdomainTask)
def test():
    """
    Run the local test suite
    """
    local("python manage.py test", fail="abort")

@task(task_class=SubdomainTask, alias="init")
def setup():
    """
    Run once to setup the site on the server.
    Setup directories, a fresh virtualenv, configuration, get code from github
    """
    
    # mkdirs
    sudo('mkdir -m 755 -p %(path)s' % env)
    sudo('chown ubuntu:ubuntu %(path)s' % env)
    run('mkdir -m 755 -p %(path)s/{httpdocs,log,django/%(project)s,virtualenv}' % env)
    # get code
    run('git clone --depth 1 --branch %(git_branch)s git://github.com/jakecr/infuse.git %(path)s/django/%(project)s' % env)
    # create virtualenv
    run('virtualenv --no-site-packages %(path)s/virtualenv' % env)

    install_requirements()
    configure()

@task(task_class=SubdomainTask)
def install_requirements():
    """
    Install requirements
    """
        
    run('pip install -E %(path)s/virtualenv -r %(path)s/django/%(project)s/requirements.txt' % env)

@task(task_class=SubdomainTask)
def configure():
    """
    Create/update config files
    """
    apache_conf = env.apache_conf.format(
        redirect_conf=server_alias(env.redirects),
        alias_conf=server_alias(env.aliases),
        **env
    )
    put(StringIO(apache_conf), '/etc/apache2/sites-available/%(domain)s' % env, use_sudo=True)
    put(StringIO(env.wsgi_conf.format(**env)), '%(path)s/django/django.wsgi' % env)
    enable()

@task(task_class=SubdomainTask)
def rollback():
    """
    Undo results of most recent update
    """
    
    # update code
    with cd('%(path)s/django/%(project)s' % env): 
        run('git reset --hard ORIG_HEAD')
    # reload python files
    run('touch %(path)s/django/django.wsgi' % env)

@task(task_class=SubdomainTask)
def disable():
    """
    Take the site down
    """

    sudo("a2dissite %(domain)s" % env)
    run("apache2ctl configtest" % env)
    sudo("apache2ctl graceful" % env)

@task(task_class=SubdomainTask)
def enable():
    """
    Re-enable a site that has been disabled
    """

    sudo("a2ensite %(domain)s" % env)
    run("apache2ctl configtest" % env)
    sudo("apache2ctl graceful" % env)

@task(task_class=SubdomainTask)
def update():
    """
    get the latest version of the site from github
    """
    
    # update code
    with cd('%(path)s/django/%(project)s' % env): 
        run('git pull' % env)
    # reload python files
    run('touch %(path)s/django/django.wsgi' % env)

@task(task_class=SubdomainTask)
def show_logs():
    """
    Show the last few lines of logs
    """
    
    run('tail %(path)s/log/error.log' % env)
    run('tail %(path)s/log/access.log' % env)

def server_alias(aliases):
    return """
        """.join(["ServerAlias "+alias for alias in aliases])

env.apache_conf = """
<VirtualHost *:80>
        # remove www
        ServerName www.{domain}
        {redirect_conf}
        RedirectPermanent / http://{domain}
</VirtualHost>

<VirtualHost *:80>
        ServerName {domain}
        {alias_conf}

        Alias /static {path}/django/{project}/website/static/
        Alias /favicon.ico {path}/django/{project}/static/favicon.ico

        WSGIDaemonProcess {project}{subdomain} python-path={path}/virtualenv/lib/python2.6/site-packages
        WSGIProcessGroup {project}{subdomain}
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

env.wsgi_conf = """
import os, sys

# put the Django project on sys.path
sys.path.insert(0, (os.path.abspath(os.path.dirname(__file__))))

os.environ['DJANGO_SETTINGS_MODULE'] = '{project}.settings'
#os.environ['PYTHON_EGG_CACHE'] = '/usr/lib/python2.4/eggcache'
from django.core.handlers.wsgi import WSGIHandler
application = WSGIHandler()
"""