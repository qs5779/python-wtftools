#!/usr/bin/env python3
# -*- Mode: Python; tab-width: 4; indent-tabs-mode: nil -*-

import os.path
import sys
from optparse import OptionParser

import mwtfpuppet


def main():
    usage = """usage: %prog [options]

  when no options are specified current flag status is shown

  """
    parser = OptionParser(usage)
    parser.add_option(
        "-c", "--clear", action="append", dest="clear", help="specify flag to clear)"
    )
    parser.add_option(
        "-d",
        "--debug",
        action="count",
        dest="debug",
        default=0,
        help="increment debug level",
    )
    parser.add_option(
        "-s", "--set", action="append", dest="set", help="specify flag to set)"
    )
    parser.add_option(
        "-t",
        "--test",
        action="store_true",
        dest="test",
        default=False,
        help="specify test mode",
    )
    parser.add_option(
        "-v",
        "--verbose",
        action="count",
        dest="verbose",
        default=0,
        help="increment verbosity level",
    )
    parser.add_option(
        "-V",
        "--version",
        action="store_true",
        dest="version",
        default=False,
        help="show version and exit",
    )

    (opts, args) = parser.parse_args()

    basenm = os.path.basename(sys.argv[0])
    options = vars(opts)
    if options["debug"] > 1:
        print(options)
        print(args)

    if options["version"]:
        print("%s Version: 1.0.0" % basenm)
        exit(0)

    options["caller"] = basenm
    flagger = mwtfpuppet.PuppetFlags(options)
    exit(flagger.cli_run())


if __name__ == "__main__":
    main()
