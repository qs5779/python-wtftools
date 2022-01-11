# -*- Mode: Python; tab-width: 4; indent-tabs-mode: nil -*-
import sys
from email.mime.text import MIMEText
from subprocess import PIPE, Popen

import mwtf


class Mailer(mwtf.Options):
    def __init__(self, opts={}):
        mopts = {"transport": "sendmail"}
        mopts.update(opts)
        super().__init__(mopts)

    def send(self, args, body):
        if self.options["transport"] == "sendmail":
            result = self.__send_sendmail(args, body)
        elif self.options["transport"] == "smtp":
            result = self.__send_smtp(args, body)
        else:
            print("NOTICE: mailer %s is not supported!" % self.options["transport"])
            result = 1
        return result

    def __send_smtp(self, args, body):
        print("NOTICE: mailer __send_smtp not implemented yet!")
        print(args, body)
        return 1

    def __send_sendmail(self, args, body):
        msg = MIMEText(body)
        msg["From"] = args.get("from", "root")
        msg["To"] = args.get("to", "root")
        if "cc" in args:
            msg["Cc"] = args["cc"]
        msg["Subject"] = args.get("subject", "No subject provided")
        p = Popen(["/usr/sbin/sendmail", "-t", "-oi"], stdin=PIPE)
        # Both Python 2.X and 3.X
        if self.isdebug():
            print(args)
            print(body)
        p.communicate(msg.as_bytes() if sys.version_info >= (3, 0) else msg.as_string())
        return p.returncode
