#!/usr/bin/env python
# vim: set filencoding=utf8
"""
Mercurial Shared SSH Repo Lock Script

@author: Mike Crute (mcrute@gmail.com)
@organization: SoftGroup Hosting
@date: February 23, 2011
"""

import os
import repolib

def main(argv):
    log = repolib.get_logger('validate-login')

    if ('SSH_HG_REPO' not in os.environ or
            'SSH_HG_USER' not in os.environ):
        log.error("Failed to execute pre-lock checks")
        return 1

    try:
        repo = repolib.Repository(os.environ['SSH_HG_REPO'])
        repo.load_from_hgrc()
    except IOError:
        log.error("Could not load repository config")
        return 1

    if not repo.can_be_written_by(os.environ['SSH_HG_USER']):
        log.error("You can not write to this repository")
        return 1

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv[1:]))
