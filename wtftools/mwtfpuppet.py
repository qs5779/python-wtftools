# frozen_string_literal: true

import configparser
import errno
import os

import mwtf
import mwtfalertable

# import re
# import sys
# from datetime import datetime


class PuppetFlags(mwtfalertable.Alerter):
    def __init__(self, opts={}):
        super().__init__(opts)
        if self.istest():
            self.flag_dir = "/tmp/flags"
        else:
            self.flag_dir = "/root/flags"

    def flags(self):
        return ["debug", "noipv6", "nowarn", "stopped"]

    def flag_fpn(self, flag):
        return os.path.join(self.flag_dir, flag + ".puppet")

    def flag_exists(self, flag):
        return os.path.exists(self.flag_fpn(flag))

    def show_flags(self):
        self.__ensure_flag_directory()
        for flag in self.flags():
            # print(flag)
            print("wtfo_puppet_%s=%s" % (flag, self.flag_exists(flag)))
        if self.istest():
            print("\ntest mode flagdir: %s" % self.flag_dir)

    def isvalid(self, flag):
        try:
            # _ignore = self.flags().index(flag)
            self.flags().index(flag)
            result = True
        except ValueError:
            self.warn("Invalid flag: " + flag)
            self.errors += 1
            result = False
        return result

    def manage(self, flag, action):
        if self.isvalid(flag):
            self.__ensure_flag_directory()
            fpn = self.flag_fpn(flag)
            exists = self.flag_exists(flag)
            if action:
                if not exists:
                    os.system("touch %s" % fpn)
            elif exists:
                os.unlink(fpn)

    def cli_run(self):
        if self.options["clear"] is not None:
            for flag in self.options["clear"]:
                self.manage(flag, False)
        if self.options["set"] is not None:
            for flag in self.options["set"]:
                self.manage(flag, True)
        self.show_flags()
        return self.errors

    def __ensure_flag_directory(self):
        if not self.istest():
            mwtf.requires_super_user
        mwtf.ensure_directory(self.flag_dir)


class PuppetConfig(PuppetFlags):
    def __init__(self, opts={}):
        super().__init__(opts)
        self.interval = None
        self.settings = None
        self.__init_pathnames()

    def setting(self, key, section="agent"):
        if self.settings is None:
            self.__load_config()
        if section in self.settings:
            return self.settings[section][key]
        self.warn("Section not found: %s" % section)
        self.errors += 1
        return ""

    def show_section(self, section="agent"):
        if self.settings is None:
            self.__load_config()
        if section in self.settings:
            print("[%s]" % section)
            for key in self.settings[section]:
                print("%s = %s" % (key, self.settings[section][key]))
        else:
            self.warn("Section not found: %s" % section)
            self.errors += 1
        return self.errors

    def show_setting(self, key, section="agent"):
        if self.settings is None:
            self.__load_config()
        if key is None:
            self.show_section(section)
        else:
            value = self.setting(key, section)
            print("[%s] %s = %s" % (section, key, value))
        return self.errors

    def show_config(self):
        if self.settings is None:
            self.__load_config()
        label = None
        for section in self.settings:
            for key in self.settings[section]:
                if section != label:
                    label = section
                    print("[%s]" % label)
                print("%s = %s" % (key, self.settings[section][key]))
        return self.errors

    def pathname(self, pathkey):
        try:
            # _ignore = self.__pathkeys().index(pathkey)
            self.__pathkeys().index(pathkey)
            key = "puppet.%s.file.status" % pathkey
            if self.pathnames[pathkey]["pn"] is None:
                args = {
                    "key": key,
                    "subject": self.pathnames[pathkey]["status"],
                    "message": "%s. Please investigate." % key,
                }
                self.raise_alert(args)
            else:
                args = {"key": key}
                self.clear(args)
            return self.pathnames[pathkey]["pn"]
        except ValueError:
            self.warn("Invalid pathkey: " + pathkey)
            self.errors += 1
            raise

    # protected

    def _run_interval(self):
        if self.interval is None:
            ri = int(self.setting("runinterval"))
            if ri:
                self.interval = int(ri)
            else:
                self.interval = 7200
        return self.interval

    def __pathkeys(self):
        return ["config", "state", "lastrun", "bin"]

    def __init_pathnames(self):
        self.pathnames = {}
        for path in self.__pathkeys():
            self.pathnames[path] = {}
            self.pathnames[path]["pn"] = None
            self.pathnames[path]["status"] = "File not found."
        self.__init_config()
        self.__init_last()
        self.__init_bin()

    def __init_file_pathname(self, choices, label, check="readable"):
        for pn in choices:
            if not os.path.exists(pn):
                continue

            good = "good"
            status = good
            if check == "executable":
                if not os.access(pn, os.X_OK):
                    status = "Unsupported attribute %s for: %s" % (check, pn)
            elif check == "readable":
                if not os.access(pn, os.R_OK):
                    status = "Unsupported attribute %s for: %s" % (check, pn)
            else:
                status = "Unsupported attribute %s for: %s" % (check, pn)

            if status == good:
                self.pathnames[label]["pn"] = pn
            self.pathnames[label]["status"] = status
            break

    def __init_config(self):
        possibles = ["/etc/puppetlabs/puppet/puppet.conf", "/etc/puppet/puppet.conf"]
        self.__init_file_pathname(possibles, "config")

    def __init_state(self):
        possibles = [
            "/opt/puppetlabs/puppet/cache/state",
            "/var/cache/puppet/state",  # debian 9 puppet
            "/var/lib/puppet/state",  # fedora 30 puppet
        ]
        self.__init_file_pathname(possibles, "state")

    def __init_bin(self):
        possibles = ["/opt/puppetlabs/bin/puppet", "/usr/bin/puppet"]
        self.__init_file_pathname(possibles, "bin", "executable")

    def __init_last(self):
        self.__init_state()

        if self.pathnames["state"]["pn"] is None:
            self.pathnames["lastrun"]["status"] = self.pathnames["state"]["status"]
            return

        possibles = [
            os.path.join(self.pathnames["state"]["pn"], "last_run_summary.yaml")
        ]
        self.__init_file_pathname(possibles, "lastrun")

    def __load_config(self):
        if self.settings is None:
            if self.pathnames["config"]["pn"] is None:
                raise FileNotFoundError(
                    errno.ENOENT,
                    "Puppet config file %s!!!" % self.pathnames["config"]["status"],
                )
            self.settings = configparser.ConfigParser()
            self.settings.read(self.pathnames["config"]["pn"])
