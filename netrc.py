# Module and documentation by Eric S. Raymond, 21 Dec 1998
# Added parsing support for password-less entries by Zsolt M, 14 Apr 2015

import os
import stat
import shlex

if os.name == 'posix':
    import pwd

__all__ = ["netrc", "NetrcParseError"]


class NetrcParseError(Exception):
    """Exception raised on syntax errors in the .netrc file."""

    def __init__(self, msg, filename=None, line_no=None):
        self.filename = filename
        self.line_no = line_no
        self.msg = msg
        Exception.__init__(self, msg)

    def __str__(self):
        return "%s (%s, line %s)" % (self.msg, self.filename, self.line_no)


class netrc:
    def __init__(self, file_path=None):
        default_netrc = file_path is None
        if file_path is None:
            try:
                file_path = os.path.join(os.environ['HOME'], ".netrc")
            except KeyError:
                raise IOError("Could not find .netrc: $HOME is not set")
        self.hosts = {}
        self.macros = {}
        with open(file_path) as fp:
            self._parse(file_path, fp, default_netrc)

    def _parse(self, file_path, fp, default_netrc):
        lexer = shlex.shlex(fp)
        lexer.wordchars += r"""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""
        lexer.commenters = lexer.commenters.replace('#', '')
        while 1:
            # Look for a machine, default, or macdef top-level keyword
            top_level = tt = lexer.get_token()
            if not tt:
                break
            elif tt[0] == '#':
                # seek to beginning of comment, in case reading the token put
                # us on a new line, and then skip the rest of the line.
                pos = len(tt) + 1
                lexer.instream.seek(-pos, 1)
                lexer.instream.readline()
                continue
            elif tt == 'machine':
                entry_name = lexer.get_token()
            elif tt == 'default':
                entry_name = 'default'
            elif tt == 'macdef':  # Just skip to end of macdefs
                entry_name = lexer.get_token()
                self.macros[entry_name] = []
                lexer.whitespace = ' \t'
                while 1:
                    line = lexer.instream.readline()
                    if not line or line == '\012':
                        lexer.whitespace = ' \t\r\n'
                        break
                    self.macros[entry_name].append(line)
                continue
            else:
                raise NetrcParseError(
                    "bad top-level token %r" % tt, file_path, lexer.lineno)

            # We're looking at start of an entry for a named machine or default.
            login = ''
            account = password = None
            self.hosts[entry_name] = {}
            while 1:
                tt = lexer.get_token()
                if tt.startswith('#') or tt in {'', 'machine', 'default', 'macdef'}:
                    if password or login:
                        self.hosts[entry_name] = (login, account, password)
                        lexer.push_token(tt)
                        break
                    else:
                        raise NetrcParseError(
                            "malformed %s entry %s terminated by %s" % (top_level, entry_name, repr(tt)),
                            file_path, lexer.lineno)
                elif tt == 'login' or tt == 'user':
                    login = lexer.get_token()
                elif tt == 'account':
                    account = lexer.get_token()
                elif tt == 'password':
                    if os.name == 'posix' and default_netrc:
                        prop = os.fstat(fp.fileno())
                        if prop.st_uid != os.getuid():
                            try:
                                f_owner = pwd.getpwuid(prop.st_uid)[0]
                            except KeyError:
                                f_owner = 'uid %s' % prop.st_uid
                            try:
                                user = pwd.getpwuid(os.getuid())[0]
                            except KeyError:
                                user = 'uid %s' % os.getuid()
                            raise NetrcParseError(
                                ("~/.netrc file owner (%s) does not match"
                                 " current user (%s)") % (f_owner, user),
                                file_path, lexer.lineno)
                        if prop.st_mode & (stat.S_IRWXG | stat.S_IRWXO):
                            raise NetrcParseError(
                                "~/.netrc access too permissive: access"
                                " permissions must restrict access to only"
                                " the owner", file_path, lexer.lineno)
                    password = lexer.get_token()
                else:
                    raise NetrcParseError("bad follower token %r" % tt, file_path, lexer.lineno)

    def authenticators(self, host):
        """Return a (user, account, password) tuple for given host."""
        if host in self.hosts:
            return self.hosts[host]
        elif 'default' in self.hosts:
            return self.hosts['default']
        else:
            return None

    def __repr__(self):
        """Dump the class data in the format of a .netrc file."""
        rep = ""
        for host in self.hosts.keys():
            attrs = self.hosts[host]
            rep = rep + "machine " + host + "\n\tlogin " + repr(attrs[0]) + "\n"
            if attrs[1]:
                rep = rep + "account " + repr(attrs[1])
            rep = rep + "\tpassword " + repr(attrs[2]) + "\n"
        for macro in self.macros.keys():
            rep = rep + "macdef " + macro + "\n"
            for line in self.macros[macro]:
                rep = rep + line
            rep += "\n"
        return rep


if __name__ == '__main__':
    print netrc()
