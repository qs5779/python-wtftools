# -*- Mode: Python; tab-width: 4; indent-tabs-mode: nil -*-

import os
import subprocess

# import distro
import mwtf


class Error(Exception):
    """Base class for exceptions in this module."""

    pass


class UsageError(Error):
    """Exception raised for errors with supplied arguments or parameters

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message


class PackageHandler(mwtf.Options):
    def validate_arg_count(self, action, args, expected, extra=False):
        nbr = len(args)
        if nbr < expected:
            raise UsageError("action %s requires %d arguments" % (action, expected))
        if (not extra) and (nbr > expected):
            raise UsageError(
                "action %s requires exactly %d arguments" % (action, expected)
            )

    def unhandled(self, action):
        print("class %s doesn't handle a file %s!" % (self.__class__.__name__, action))
        return 1

    def file_action(self, args):
        return self.unhandled("file")

    def find_action(self, args):
        return self.unhandled("find")

    def info_action(self, args):
        return self.unhandled("info")

    def install_action(self, args):
        return self.unhandled("install")

    def uninstall_action(self, args):
        return self.unhandled("uninstall")

    def list_package(self, args):
        return self.unhandled("list package")

    def list_packages(self):
        return self.unhandled("list packages")

    def action(self, action, args):
        if (self.options["debug"] > 0) or (self.options["verbose"] > 0):
            print("action: " + action)
            print("args: ", args)
        if action == "file":
            self.validate_arg_count(action, args, 1)
            result = self.file_action(args)
        elif (action == "find") or (action == "search"):
            self.validate_arg_count(action, args, 1)
            result = self.find_action(args)
        elif action == "info":
            self.validate_arg_count(action, args, 1)
            result = self.info_action(args)
        elif action == "install":
            self.validate_arg_count(action, args, 1, True)
            result = self.install_action(args)
        elif action == "uninstall":
            self.validate_arg_count(action, args, 1, True)
            result = self.uninstall_action(args)
        elif action == "list":
            if len(args) > 0:
                self.validate_arg_count(action, args, 1)
                result = self.list_package(args)
            else:
                print("calling list packages")
                result = self.list_packages()
        else:
            raise ValueError(action + " is not a valid action!!!")
        return result

    def execute(self, cmd):
        try:
            subprocess.check_call(cmd)
            result = 0
        except subprocess.CalledProcessError as cpex:
            if (self.options["debug"] > 0) or (self.options["verbose"] > 0):
                print(cpex)
            result = cpex.returncode
        except Exception as ex:
            print(ex)
            result = 1
        return result

    def output_if(self, cmd):
        if self.options["output"] is not None:
            if self.options["quiet"]:
                cmd += " > %s" % self.options["output"]
            else:
                cmd += " | tee %s" % self.options["output"]
        return os.system(cmd)


class PacmanHandler(PackageHandler):
    def list_package(self, args):
        return self.output_if("pacman -Ql %s" % args[0])

    def list_packages(self):
        result = self.output_if("pacman -Qe")
        return result

    def file_action(self, args):
        return self.execute(["pacman", "-Qo", args[0]])

    def info_action(self, args):
        return self.execute(["pacman", "-Qi", args[0]])

    def find_action(self, args):
        switches = "-Ss"
        if self.options["refresh"]:
            mwtf.requires_super_user
            switches += "y"
        return self.execute(["pacman", switches, args[0]])

    def install_action(self, args):
        mwtf.requires_super_user
        switches = "-S"
        if self.options["refresh"]:
            switches = +"y"
        cmd = ["pacman", switches]
        for i in args:
            cmd.append(i)
        return self.execute(cmd)

    def uninstall_action(self, args):
        mwtf.requires_super_user
        cmd = ["pacman", "-R"]
        for i in args:
            cmd.append(i)
        return self.execute(cmd)


class AptHandler(PackageHandler):
    def list_package(self, args):
        return self.output_if("dpkg -L %s" % args[0])

    def list_packages(self):
        result = self.output_if(r"apt list --installed | sort")
        return result

    def file_action(self, args):
        return self.execute(["dpkg", "-S", args[0]])

    def info_action(self, args):
        return self.execute(["apt-cache", "show", args[0]])

    def find_action(self, args):
        if self.options["refresh"]:
            mwtf.requires_super_user
            self.execute(["apt", "update"])
        cmd = ["apt", "search"]
        if self.options["names-only"] is not None:
            cmd.append("--names-only")
        cmd.append(args[0])
        return self.execute(cmd)

    def install_action(self, args):
        mwtf.requires_super_user
        if self.options["refresh"]:
            self.execute(["apt", "update"])
        cmd = ["apt", "install"]
        for i in args:
            cmd.append(i)
        return self.execute(cmd)

    def uninstall_action(self, args):
        mwtf.requires_super_user
        cmd = ["apt", "remove"]
        for i in args:
            cmd.append(i)
        return self.execute(cmd)


class YumHandler(PackageHandler):
    def __init__(self, opts={}):
        PackageHandler.__init__(self, opts)  # python2 compatibility
        self.pkgcmd = "yum"

    def list_package(self, args):
        return self.output_if("rpm -ql %s" % args[0])

    def list_packages(self):
        result = self.output_if(
            "rpm -qa --qf '%{name}-%{version}-%{release}.%{arch}.rpm\\n' | sort"
        )
        return result

    def file_action(self, args):
        return self.execute(["rpm", "-qf", args[0]])

    def info_action(self, args):
        return self.execute(["rpm", "-qi", args[0]])

    def find_action(self, args):
        cmd = [self.pkgcmd, "search", args[0]]
        if self.options["refresh"]:
            mwtf.requires_super_user
            cmd.insert(1, "--refresh")
        return self.execute(cmd)

    def install_action(self, args):
        mwtf.requires_super_user
        cmd = [self.pkgcmd, "install"]
        for i in args:
            cmd.append(i)
        if self.options["refresh"]:
            cmd.insert(1, "--refresh")
        return self.execute(cmd)

    def uninstall_action(self, args):
        mwtf.requires_super_user
        cmd = [self.pkgcmd, "remove"]
        for i in args:
            cmd.append(i)
        return self.execute(cmd)


class DnfHandler(YumHandler):
    def __init__(self, opts={}):
        YumHandler.__init__(self, opts)  # python2 compatibility
        self.pkgcmd = "dnf"
        if self.options["test"]:
            print("created instance of DnfHandler")
