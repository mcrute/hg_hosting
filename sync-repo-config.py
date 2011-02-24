#!/usr/bin/env python
# vim: set filencoding=utf8
"""
Mercurial Shared SSH Repository Metadat Sync

@author: Mike Crute (mcrute@gmail.com)
@organization: SoftGroup Hosting
@date: February 23, 2011
"""

import repolib


def sync_repository_config(repos, users, log):
    for repo in repos:
        if repo.exists:
            log.info("Writing hgrc for %r", repo.path)
            repo.write_hgrc(users)
        else:
            log.warn("Non-existent repo %r", repo.path)


def sync_ssh_config(auth_keys_filename, users, log):
    with open(auth_keys_filename, 'w') as auth_keys:
        log.info("Writing %r", auth_keys_filename)

        for user in users:
            log.info("Writing user '%s'", user)
            auth_keys.write(user.ssh_line)


def main(argv):
    log = repolib.get_logger('sync-repo-config')

    try:
        cfg_file = argv[-1] if argv else "/etc/hgssh.cfg"
        cfg = repolib.ConfigLoader(cfg_file)
    except IOError:
        log.error("Config file %r doesn't exist", cfg_file)
        return 1

    sync_repository_config(cfg.repos, cfg.user_dict, log)

    try:
        sync_ssh_config(cfg.repo_user_authorized_keys, cfg.users, log)
    except ValueError, exc:
        log.error("%s", exc)
        return 1

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv[1:]))
