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


def check_repo(env, log):
    repo = repolib.Repository(env['SSH_HG_REPO'])
    repo.load_from_hgrc()

    if not repo.can_be_written_by(env['SSH_HG_USER']):
        log.error("You can not write to this repository.")
        return 1

    return 0


def main(argv):
    log = repolib.get_logger('validate-login')

    try:
        return check_repo(os.environ, log)

    except IOError:
        log.error("Could not load repository config.")
        log.error("Failed to execute pre-lock checks.")
        return 1

    except KeyError:
        log.error("Incomplete or corrupted environment.")
        log.error("Failed to execute pre-lock checks.")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv[1:]))
