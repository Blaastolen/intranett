import os

from fabric.api import cd, env, run, sudo, settings, hide, get

env.shell = "/bin/bash -c"
home = '/srv/jarn'

def svn_info():
    with cd(home):
        sudo('pwd && svn info', user='jarn')

def dump_db():
    with cd(home):
        sudo('rm var/snapshotbackups/*', user='jarn')
        sudo('bin/snapshotbackup', user='jarn')

def download_last_dump():
    with settings(hide('warnings', 'running', 'stdout', 'stderr'),
                  warn_only=True):
        existing = sudo('ls -rt1 %s/var/snapshotbackups/*' % home, user='jarn')
    for e in existing.split('\n'):
        get(e, os.path.join(os.getcwd(), 'var', 'snapshotbackups'))

def init_server():
    home = '/home/hannosch'
    # set up environment variables
    with settings(hide('stdout', 'stderr')):
        profile = run('cat %s/.bash_profile' % home)
    profile_lines = profile.split('\n')
    exports = [l for l in profile_lines if l.startswith('export INTRANETT_')]
    if len(exports) < 2:
        start, end = profile_lines[:2], profile_lines[2:]
        subdomain = env.host_string
        domain_line = 'export INTRANETT_DOMAIN=%s.intranett.no\n' % subdomain
        with settings(hide('stdout', 'stderr')):
            front_ip = run('/sbin/ifconfig ethfe | head -n 2 | tail -n 1')
        front_ip = front_ip.lstrip('inet addr:').split()[0]
        front_line = 'export INTRANETT_ZOPE_IP=%s' % front_ip

        new_file = start + [front_line] + [domain_line] + end
        run('echo -e "{content}" > {home}/.bash_profile'.format(
            home=home, content='\n'.join(new_file)))

    # set cron mailto
    with settings(hide('stdout'), warn_only=True):
        # if no crontab exists, this crontab -l has an exit code of 1
        run('crontab -l > %s/crontab.tmp' % home)
        crontab = run('cat %s/crontab.tmp' % home)
    cron_lines = crontab.split('\n')
    mailto = [l for l in cron_lines if l.startswith('MAILTO')]
    if not mailto:
        # add mailto right after the comments
        new_cron_lines = []
        added = False
        for line in cron_lines:
            if line.startswith('#'):
                new_cron_lines.append(line)
            else:
                if not added:
                    # XXX hosting@jarn.com
                    cron_lines.append('MAILTO=hanno@jarn.com')
                    added = True
                new_cron_lines.append(line)
        with settings(hide('stdout', 'stderr')):
            run('echo -e "{content}" > {home}/crontab.tmp'.format(
                home=home, content='\n'.join(new_cron_lines)))
            run('crontab %s/crontab.tmp' % home)
    with settings(hide('stdout', 'stderr')):
        run('rm %s/crontab.tmp' % home)
