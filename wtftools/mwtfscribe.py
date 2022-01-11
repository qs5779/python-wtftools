# -*- Mode: Python; tab-width: 4; indent-tabs-mode: nil -*-

import logging
import logging.handlers
import sys

import mwtf

try:
    from systemd.journal import JournalHandler
except ImportError:
    gJournal = False
else:
    gJournal = True


class Scribe(mwtf.Options):
    def __init__(self, opts={}):
        sopts = {
            "quiet": False,
            "loud": False,
            "screen": sys.stdout.isatty(),
        }
        sopts.update(opts)
        super().__init__(sopts)

        self.log = logging.getLogger("wtfo")

        if ("level" not in self.options) or (self.options["level"] is None):
            if self.options["debug"]:
                self.options["level"] = logging.DEBUG
            elif self.options["verbose"]:
                self.options["level"] = logging.INFO
            else:
                self.options["level"] = logging.WARNING

        if ("logfile" in self.options) and (self.options["logfile"] is not None):
            logging.basicConfig(
                filename=self.options["logfile"], format="%(asctime)s - %(message)s"
            )
        elif gJournal:
            self.log.addHandler(
                JournalHandler(SYSLOG_IDENTIFIER=self.options["caller"])
            )
        else:
            # TODO: SYSLOG_IDENTIFIER=self.options['caller']
            self.log.addHandler(logging.handlers.SysLogHandler(address="/dev/log"))

        self.log.setLevel(self.options["level"])

        if self.options["loud"] and not self.options["screen"]:
            self.options["screen"] = True
        if self.options["quiet"] and self.options["screen"]:
            self.options["screen"] = False

        if self.options["screen"]:
            console = logging.StreamHandler()
            console.setLevel(self.options["level"])
            # set a format which is simpler for console use
            formatter = logging.Formatter("%(levelname)8s: %(message)s")
            # tell the handler to use this format
            console.setFormatter(formatter)
            self.log.addHandler(console)

    def debug(self, message, *args, **kwargs):
        self.log.debug(message, *args, **kwargs)

    def info(self, message, *args, **kwargs):
        self.log.info(message, *args, **kwargs)

    def warn(self, message, *args, **kwargs):
        self.log.warning(message, *args, **kwargs)

    def error(self, message, *args, **kwargs):
        self.log.error(message, *args, **kwargs)
        self.errors += 1

    def fatal(self, message, *args, **kwargs):
        self.log.critical(message, *args, **kwargs)
        self.errors += 1

    def unknown(self, message, *args, **kwargs):
        self.log.log(self.options["level"], message, *args, **kwargs)
