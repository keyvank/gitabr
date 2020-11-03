from django.shortcuts import render
from django.http import HttpResponse
import git
import os
from .models import GitApp
import docker
import urllib
import io

ROOT = '/home/keyvan/sites'
doc = docker.from_env()


HOP_BY_HOP = ['Connection','Keep-Alive','Proxy-Authenticate','Proxy-Authorization','TE','Trailers','Transfer-Encoding','Upgrade']
def proxy(request, path, port):
    url = "http://127.0.0.1:{}{}".format(port, path)
    if request.GET:
        url += '?' + urlencode(request.GET)
    def convert(s):
        s = s.replace('HTTP_','',1)
        s = s.replace('_','-')
        return s

    request_headers = dict((convert(k),v) for k,v in request.META.items() if k.startswith('HTTP_'))
    request_headers['CONTENT-TYPE'] = request.META.get('CONTENT_TYPE', '')
    request_headers['CONTENT-LENGTH'] = request.META.get('CONTENT_LENGTH', '')

    if request.method == "GET":
        data = None
    else:
        data = request.raw_post_data
    downstream_request = urllib.request.Request(url, data, headers=request_headers)
    response = urllib.request.urlopen(downstream_request)
    r = HttpResponse(response.read())
    for header in response.info().keys():
        if header not in HOP_BY_HOP:
            r[header] = response.info()[header]
    return r

def run(path, uid, port):
    link = '{}/tcp'.format(port)
    try:
        cont = doc.containers.get(uid)
        if cont.status != 'running':
            cont.start()
    except docker.errors.NotFound:
        doc.images.build(path=path, tag=uid)
        cont = doc.containers.run(uid, ports={link: None}, detach=True, name=uid)

    return int(cont.attrs['NetworkSettings']['Ports'][link][0]['HostPort'])

def serve(request, user, repo, rest):

    url = 'https://github.com/{}/{}'.format(user, repo)
    uid = 'github-{}-{}'.format(user, repo)

    user_dir = os.path.join(ROOT, user)
    repo_dir = os.path.join(user_dir, repo)

    os.makedirs(user_dir, exist_ok = True)
    app, _ = GitApp.objects.get_or_create(url = url, root = repo_dir)
    if not os.path.exists(repo_dir):
        git.Git(user_dir).clone(url)

    r = git.Repo(repo_dir)
    o = r.remotes.origin
    o.pull()

    if os.path.exists(os.path.join(repo_dir, '.gitabr')):
        with io.open(os.path.join(repo_dir, '.gitabr')) as f:
            web_port = int(f.read())
    else:
        web_port = 80

    port = run(repo_dir, uid, web_port)

    return proxy(request, rest, port)
