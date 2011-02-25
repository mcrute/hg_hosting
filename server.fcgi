#!/usr/bin/env python
# vim: set filencoding=utf8
"""
HGWeb WSGI Application Host

@author: Mike Crute (mcrute@gmail.com)
@organization: SoftGroup Interactive, Inc.
@date: February 25, 2011
"""

from flup.server.fcgi_fork import WSGIServer
from mercurial import demandimport; demandimport.enable()
from mercurial.hgweb.hgwebdir_mod import hgwebdir


WSGIServer(hgwebdir('/etc/hgweb.cfg'),
    bindAddress='/tmp/hgserver.sock',
    maxRequests=10, minSpare=1, maxSpare=3,
    maxChildren=3).run()
