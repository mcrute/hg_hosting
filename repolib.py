# vim: set filencoding=utf8
"""
Mercurial Repository Management Library

@author: Mike Crute (mcrute@gmail.com)
@organization: SoftGroup Hosting
@date: February 23, 2011
"""

import os.path
import logging
from StringIO import StringIO
from ConfigParser import SafeConfigParser


class Adornments(object):

    BASE_CSS = ("padding: 0px 4px;" "font-size: 10px;"
                "font-weight: normal;" "border: 1px solid;"
                "background-color: #fafafa;"
                "border-color: #ffffff #f0f0f0 #f0f0f0 #ffffff;")

    CSS_YELLOW = ("background-color: #ffe500;" "color: #222222;"
                  "border-color: #fff066 #a89e43 #a89e43 #fff066;")

    CSS_BROWN = ("background-color: #815555;" "color: #ffffff;"
                 "border-color: #ff3347 #541118 #541118 #ff3347;")

    CSS_GREEN = ("background-color: #11a800;" "color: #ffffff;"
                 "border-color: #5eff4c #3ea832 #3ea832 #5eff4c;")

    CSS_BLUE = ("background-color: #0099ff;" "color: #ffffff;"
                "border-color: #4cb8ff #3279a8 #3279a8 #4cb8ff;")

    CSS_RED = ("background-color: #ff0000;" "color: #ffffff;"
               "border-color: #ff6666 #000000 #000000 #ff6666;")

    BASE_HTML = '<span style="{0}{{css}}">{{tag}}</span> '.format(BASE_CSS)
    LINK_CSS_DARK = 'color: #ffffff; text-decoration: none;'
    LINK_CSS_LIGHT = 'color: #000000; text-decoration: none;'

    def __init__(self, repo):
        self.repo = repo

    def __str__(self):
        if self.repo.moved_to:
            tag = '<a style="{link_css}" href="{url}">MOVED</a>'
            tag = tag.format(link_css=self.LINK_CSS_DARK,
                                url=self.repo.moved_to)
            return self.BASE_HTML.format(css=self.CSS_BLUE, tag=tag)

        if self.repo.defunct:
            return self.BASE_HTML.format(css=self.CSS_BROWN, tag="DEFUNCT")

        if self.repo.upstream:
            tag = '<a style="{link_css}" href="{url}">FORK</a>'
            tag = tag.format(link_css=self.LINK_CSS_LIGHT,
                                url=self.repo.upstream)
            return self.BASE_HTML.format(css=self.CSS_YELLOW, tag=tag)

        return ""


class Repository(object):

    def __init__(self, path, description=None, contact=None):
        self.path = path
        self.description = description
        self.contact = contact
        self.readers = []
        self.writers = []
        self.defunct = False
        self.moved_to = None
        self.repo_path = None
        self.upstream = None
        self.lock_script = None

    def can_be_read_by(self, user):
        return user in self.readers

    def can_be_written_by(self, user):
        return user in self.writers

    @property
    def exists(self):
        return os.path.exists(self.full_path)

    @property
    def full_path(self):
        return os.path.join(self.repo_path, self.path)

    @property
    def hgrc_path(self):
        return os.path.join(self.full_path, '.hg', 'hgrc')

    @classmethod
    def from_config(cls, config, repo_path, lock_script=None):
        self = cls(config['path'], config.get('description', None),
                   config.get('contact', None))

        self.readers = ConfigLoader.as_list(config.get('read', ''))
        self.writers = ConfigLoader.as_list(config.get('write', ''))

        self.defunct = ConfigLoader.as_bool(config.get('defunct', 'no'))
        self.moved_to = config.get('moved_to', None)
        self.upstream = config.get('upstream', None)
        self.upstream = config.get('upstream', None)

        self.repo_path = repo_path
        self.lock_script = lock_script

        return self

    def build_hgrc(self, users):
        buf = StringIO()

        buf.write("# This file is generated by sync-repo-config\n")
        buf.write("# Changes are over-written on each run\n\n")

        if self.contact or self.description or self.writers:
            buf.write("[web]\n")

            if self.contact:
                buf.write("contact = {0}\n".format(users[self.contact]))

            if self.description:
                buf.write("description = {adornments}"
                          " {self.description}\n".format(
                              adornments=Adornments(self), self=self))

            if self.writers:
                buf.write("allow_push = {0}\n".format(",".join(self.writers)))

            buf.write("\n")

        if self.lock_script:
            buf.write("[hooks]\n")
            buf.write("pretxnchangegroup.deny.lock = {0}\n".format(
                        self.lock_script))
            buf.write("\n")

        buf.write("[ssh]\n")
        buf.write("readers = {0}\n".format(",".join(self.readers)))
        buf.write("writers = {0}\n".format(",".join(self.writers)))

        return buf.getvalue()

    def write_hgrc(self, users):
        if not self.exists:
            raise IOError("Repository {0!r} does not exist".format(
                    self.full_path))

        with open(self.hgrc_path, 'w') as hgrc:
            hgrc.write(self.build_hgrc(users))

    def load_hgrc(self):
        hgrc = SafeConfigParser()
        with open(self.hgrc_path, 'r') as fp:
            hgrc.readfp(fp)

        return hgrc

    def load_from_hgrc(self):
        hgrc = self.load_hgrc()

        self.description = hgrc.get("web", "description")
        self.contact = hgrc.get("web", "contact")
        self.readers = ConfigLoader.as_list(hgrc.get("ssh", "readers"))
        self.writers = ConfigLoader.as_list(hgrc.get("ssh", "writers"))


class User(object):

    def __init__(self, username, name, email):
        self.username = username
        self.name = name
        self.email = email
        self.can_create = False
        self.ssh_key = None
        self.login_script = None

    def __str__(self):
        return "{self.name} <{self.email}>".format(self=self)

    @classmethod
    def from_config(cls, config, login_script):
        self = cls(config['username'], config['name'], config['email'])

        self.can_create = ConfigLoader.as_bool(config['can_create'])
        self.ssh_key = config['ssh_key']
        self.login_script = login_script

        return self

    @property
    def ssh_line(self):
        return ('command="{self.login_script} {self.username}",'
                'no-port-forwarding,no-X11-forwarding,no-agent-forwarding'
                ' {self.ssh_key} {self.email}\n').format(self=self)


class ConfigLoader(object):

    def __init__(self, cfg_file):
        self.config = SafeConfigParser()
        with open(cfg_file, 'r') as config_file:
            self.config.readfp(config_file)

        self.login_script = self.config.get('system', 'login_script')
        self.repo_path = self.config.get('system', 'repo_path')
        self.repo_user = self.config.get('system', 'repo_user')
        self.lock_script = self.config.get('system', 'lock_script')

    def _filtered_sections(self, section_name):
        for section in self.config.sections():
            if section.startswith(section_name + ":"):
                yield section

    @staticmethod
    def as_bool(value):
        return value.lower() in ('yes', 'true', 'on')

    @staticmethod
    def as_list(value):
        return [item.strip() for item in value.split(",")
                    if value]

    @staticmethod
    def clean_section_name(name):
        return name.split(':')[1]

    @property
    def repos(self):
        for section in self._filtered_sections('repo'):
            values = dict(self.config.items(section))
            values['path'] = self.clean_section_name(section)

            yield Repository.from_config(values, self.repo_path,
                                            self.lock_script)

    @property
    def users(self):
        for section in self._filtered_sections('user'):
            values = dict(self.config.items(section))
            values['username'] = self.clean_section_name(section)

            yield User.from_config(values, self.login_script)

    @property
    def user_dict(self):
        return dict((user.username, user) for user in self.users)

    @property
    def repo_user_authorized_keys(self):
        home_dir = os.path.expanduser('~' + self.repo_user)

        if '~' in home_dir:
            raise ValueError("User {0!r} doesn't exist".format(self.repo_user))

        return os.path.join(home_dir, '.ssh', 'authorized_keys')


def get_logger(name):
    format = "%(levelname)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=format,
                        filename="scripts.log")

    stream = logging.StreamHandler()
    stream.setLevel(logging.WARNING)
    stream.setFormatter(logging.Formatter(format))

    logger = logging.getLogger(name)
    logger.addHandler(stream)

    return logger
