#!/usr/bin/env python
# Software License Agreement (BSD License)
#
# Copyright (c) 2009, Willow Garage, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Willow Garage, Inc. nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

"""
Build debs for a package and all of its dependencies as necessary
"""

import roslib; roslib.load_manifest('rosdeb')

import os
import sys
import subprocess
import shutil
import tempfile
import yaml
import urllib2
import stat
import tempfile

import rosdeb
from rosdeb.rosutil import checkout_svn_to_tmp

from roslib2.distro import Distro
from rosdeb.core import ubuntu_release, debianize_name, debianize_version, platforms, ubuntu_release_name

NAME = 'list_missing.py' 
TARBALL_URL = "https://code.ros.org/svn/release/download/stacks/%(stack_name)s/%(base_name)s/%(f_name)s"

import traceback

def load_info(stack_name, stack_version):
    import urllib
    
    base_name = "%s-%s"%(stack_name, stack_version)
    f_name = base_name + '.yaml'

    url = TARBALL_URL%locals()

    try:
        return yaml.load(urllib2.urlopen(url))
    except:
        print >> sys.stderr, "Problem fetching yaml info for %s %s (%s)"%(stack_name, stack_version, url)
        sys.exit(1)

def compute_deps(distro, stack_name):

    seen = set()
    ordered_deps = []

    def add_stack(s):
        if s in seen:
            return
        if s not in distro.stacks:
            print >> sys.stderr, "[%s] not found in distro."%(s)
            sys.exit(1)
        seen.add(s)
        v = distro.stacks[s].version
        si = load_info(s, v)
        for d in si['depends']:
            add_stack(d)
        ordered_deps.append((s,v))

    if stack_name == 'ALL':
        for s in distro.stacks.keys():
            add_stack(s)
    else:
        add_stack(stack_name)

    return ordered_deps


def deb_in_repo(deb_name, deb_version, os_platform, arch):
    # Retrieve the package list from the shadow repo
    packageurl="http://code.ros.org/packages/ros-shadow/ubuntu/dists/%(os_platform)s/main/binary-%(arch)s/Packages"%locals()
    packagelist = urllib2.urlopen(packageurl).read()
    str = 'Package: %s\nVersion: %s'%(deb_name, deb_version)
    return str in packagelist


def list_missing(distro_name, os_platform, arch):

    # Load the distro from the URL
    # TODO: Should this be done from file in release repo instead (and maybe updated in case of failure)
    distro_uri = "https://code.ros.org/svn/release/trunk/distros/%s.rosdistro"%distro_name
    distro = Distro(distro_uri)

    # Find all the deps in the distro for this stack
    deps = compute_deps(distro, 'ALL')

    missing_primary = set()
    missing_dep = set()

    # Build the deps in order
    for (sn, sv) in deps:
        deb_name = "ros-%s-%s"%(distro_name, debianize_name(sn))
        deb_version = debianize_version(sv, '0', os_platform)
        if not deb_in_repo(deb_name, deb_version, os_platform, arch):
            si = load_info(sn, sv)
            depends = set(si['depends'])
            if depends.isdisjoint(missing_primary.union(missing_dep)):
                missing_primary.add(sn)
            else:
                missing_dep.add(sn)

    print "For %s %s %s:"%(distro_name, os_platform, arch)
    print "The following stacks are missing but have deps satisfied: "
    print missing_primary
    print "The following stacks are missing deps: "
    print missing_dep

def list_missing_main():

    from optparse import OptionParser
    parser = OptionParser(usage="usage: %prog <distro> <os-platform> <arch>", prog=NAME)


    (options, args) = parser.parse_args()

    if len(args) != 3:
        parser.error('invalid args')
        
    (distro_name, os_platform, arch) = args

    list_missing(distro_name, os_platform, arch)
        
if __name__ == '__main__':
    list_missing_main()
