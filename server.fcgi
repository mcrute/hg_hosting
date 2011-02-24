#!/usr/bin/env python

from flup.server.fcgi_fork import WSGIServer
from mercurial import demandimport; demandimport.enable()
from mercurial.hgweb.hgwebdir_mod import hgwebdir


WSGIServer(hgwebdir('/etc/hgweb.cfg'),
    bindAddress='/tmp/hgserver.sock',
    maxRequests=10, minSpare=1, maxSpare=3,
    maxChildren=3).run()
