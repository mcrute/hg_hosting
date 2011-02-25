#!/usr/bin/env python
# vim: set filencoding=utf8
"""
Mercurial Shared SSH Login Validator

@author: Mike Crute (mcrute@gmail.com)
@organization: SoftGroup Hosting
@date: February 23, 2011
"""

import re
import os
import repolib

from mercurial import demandimport; demandimport.enable()
from mercurial import dispatch


def parse_path():
    cmd = os.environ.get('SSH_ORIGINAL_COMMAND', '')
    path = re.match("hg -R (\S+) serve --stdio", cmd)

    if path:
        return path.groups()[0]

    return None


def main(argv):
    log = repolib.get_logger('validate-login')
    user = argv[-1]
    path = parse_path()

    log.debug("Validating login for %r on %r", user, path)

    if path:
        repo = repolib.Repository(path)
        repo.repo_path = os.getcwd()
    else:
        log.error("Invalid command")
        return 1

    if not repo.exists:
        log.error("Repo %s does not exist", repo.full_path)
        return 1

    try:
        repo.load_from_hgrc()
    except IOError:
        log.error("Could not read repo config")
        return 1

    if not repo.can_be_read_by(user):
        log.error("You can not read this repository")
        return 1

    os.environ['SSH_HG_USER'] = user
    os.environ['SSH_HG_REPO'] = repo.full_path

    log.debug("All checks passed, serving.")
    dispatch.dispatch(['-R', path, 'serve', '--stdio'])


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv[1:]))
