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
import roslib; roslib.load_manifest('test_rosinstall')

import os
import stat
import struct
import sys
import unittest
import subprocess
import tempfile
import urllib
import shutil
import roslib
import rostest

import rosinstall


class RosinstallCommandlineTest(unittest.TestCase):

    def setUp(self):
        #self.rosinstall_tempfile = tempfile.NamedTemporaryFile(mode='a+b')
        self.rosinstall_fn = ["rosrun", "rosinstall", "rosinstall"]
        #urllib.urlretrieve("https://code.ros.org/svn/ros/installers/trunk/rosinstall/rosinstall2", self.rosinstall_fn)
        #os.chmod(self.rosinstall_fn, stat.S_IRWXU)
        self.directories = {}


    def tearDown(self):
        for d in self.directories:
            shutil.rmtree(self.directories[d])
        #os.remove(self.rosinstall_fn)

    def test_Rosinstall_executable(self):
        cmd = self.rosinstall_fn
        print cmd.append("-h")
        self.assertEqual(0,subprocess.call(cmd))

    def test_Rosinstall_ros(self):
        directory = tempfile.mkdtemp()
        self.directories["ros"] = directory
        cmd = self.rosinstall_fn
        cmd.extend([directory, os.path.join(roslib.packages.get_pkg_dir("test_rosinstall"), "rosinstalls", "ros_w_release.rosinstall")])
        self.assertEqual(0,subprocess.call(cmd))
        shutil.rmtree(directory)
        self.directories.pop("ros")

    def DISABLED_test_Rosinstall_ros_stack(self):
        directory = tempfile.mkdtemp()
        self.directories["stack"] = directory
        cmd = self.rosinstall_fn
        cmd.extend([directory, os.path.join(roslib.packages.get_pkg_dir("test_rosinstall"), "rosinstalls", "distro_stack.rosinstall")])
        self.assertEqual(0,subprocess.call(cmd))
        shutil.rmtree(directory)
        self.directories.pop("stack")

    def DISABLED_test_Rosinstall_ros_variant(self):
        directory = tempfile.mkdtemp()
        self.directories["variant"] = directory
        cmd = self.rosinstall_fn
        cmd.extend([directory, os.path.join(roslib.packages.get_pkg_dir("test_rosinstall"), "rosinstalls", "distro_variant.rosinstall")])
        self.assertEqual(0,subprocess.call(cmd))
        shutil.rmtree(directory)
        self.directories.pop("variant")


class RosinstallCommandlineOverlays(unittest.TestCase):

    def setUp(self):
        self.rosinstall_tempfile = tempfile.NamedTemporaryFile(mode='a+b')
        self.rosinstall_fn = ["rosrun", "rosinstall", "rosinstall"]
        #self.rosinstall_fn = "/tmp/test_rosinstall_temp_version"
        #urllib.urlretrieve("https://code.ros.org/svn/ros/installers/trunk/rosinstall/rosinstall", self.rosinstall_fn)
        #os.chmod(self.rosinstall_fn, stat.S_IRWXU)
        self.directories = {}
        self.base = tempfile.mkdtemp()
        cmd = self.rosinstall_fn[:]
        #cmd.extend([self.base, "http://www.ros.org/rosinstalls/boxturtle_base.rosinstall"])
        cmd.extend([self.base, os.path.join(roslib.packages.get_pkg_dir("test_rosinstall"), "rosinstalls", "ros_w_release.rosinstall")])
        self.assertEqual(0,subprocess.call(cmd))


    def tearDown(self):
        for d in self.directories:
            shutil.rmtree(self.directories[d])
        shutil.rmtree(self.base)
        #os.remove(self.rosinstall_fn)

    def test_Rosinstall_rosinstall_file_generation(self):
        generated_rosinstall_filename = os.path.join(self.base, ".rosinstall")
        self.assertTrue(os.path.exists(generated_rosinstall_filename))
        source_yaml = rosinstall.helpers.get_yaml_from_uri(generated_rosinstall_filename)
        self.assertEqual(source_yaml, 
                         [{'svn': { 'uri': 'https://code.ros.org/svn/ros/stacks/ros/tags/boxturtle',
                                    'local-name': 'ros'} },
                          {'svn': { 'uri': 'https://code.ros.org/svn/ros/stacks/ros_release/trunk',
                                    'local-name': 'ros_release'} }
                          ])

        
            

    def test_Rosinstall_common_msgs_as_explicit_overlay(self):
        self.assertEqual(self.rosinstall_fn, ["rosrun", "rosinstall", "rosinstall"])
        directory = tempfile.mkdtemp()
        with tempfile.NamedTemporaryFile() as ri_file:
            file_text = """
- other:
    local-name: %s/ros_release
- other:
    local-name: %s/ros
- svn:
    uri: https://code.ros.org/svn/ros-pkg/stacks/common_msgs/tags/boxturtle
    local-name: stacks/common_msgs
"""%(self.base, self.base)
            print file_text
            ri_file.write(file_text)
            ri_file.flush()
                          
            self.directories["tutorials"] = directory
            cmd = self.rosinstall_fn[:]
            cmd.extend([directory, ri_file.name])
            print "EXECUTING", cmd
            self.assertEqual(0,subprocess.call(cmd))

        shutil.rmtree(directory)
        self.directories.pop("tutorials")

    def test_Rosinstall_ros_tutorial_as_argument(self):
        directory = tempfile.mkdtemp()
        self.directories["tutorials2"] = directory
        cmd = self.rosinstall_fn[:]
        cmd.extend([directory, self.base, os.path.join(roslib.packages.get_pkg_dir("test_rosinstall"), "rosinstalls", "overlay.rosinstall")])
        print "Running command %s"%cmd
        self.assertEqual(0,subprocess.call(cmd))


        shutil.rmtree(directory)
        self.directories.pop("tutorials2")

class RosinstallOptionsTest(unittest.TestCase):

    def setUp(self):
        #self.rosinstall_tempfile = tempfile.NamedTemporaryFile(mode='a+b')
        self.rosinstall_fn = ["rosrun", "rosinstall", "rosinstall"]
        #urllib.urlretrieve("https://code.ros.org/svn/ros/installers/trunk/rosinstall/rosinstall2", self.rosinstall_fn)
        #os.chmod(self.rosinstall_fn, stat.S_IRWXU)
        self.directories = {}


    def tearDown(self):
        for d in self.directories:
            shutil.rmtree(self.directories[d])
        #os.remove(self.rosinstall_fn)


    def test_rosinstall_delete_changes(self):
        directory = tempfile.mkdtemp()
        self.directories["delete"] = directory
        cmd = self.rosinstall_fn
        cmd.extend([directory, os.path.join(roslib.packages.get_pkg_dir("test_rosinstall"), "rosinstalls", "simple.rosinstall"), "-n"])
        self.assertEqual(0,subprocess.call(cmd))

        cmd.extend([directory, os.path.join(roslib.packages.get_pkg_dir("test_rosinstall"), "rosinstalls", "simple_changed_uri.rosinstall"), "--delete-changed-uri", "-n"])
        self.assertEqual(0,subprocess.call(cmd))

        shutil.rmtree(directory)
        self.directories.pop("delete")

    def test_rosinstall_abort_changes(self):
        directory = tempfile.mkdtemp()
        self.directories["abort"] = directory
        cmd = self.rosinstall_fn
        cmd.extend([directory, os.path.join(roslib.packages.get_pkg_dir("test_rosinstall"), "rosinstalls", "simple.rosinstall"), "-n"])
        self.assertEqual(0,subprocess.call(cmd))

        cmd.extend([directory, os.path.join(roslib.packages.get_pkg_dir("test_rosinstall"), "rosinstalls", "simple_changed_uri.rosinstall"), "--abort-changed-uri", "-n"])
        self.assertEqual(1,subprocess.call(cmd))

        shutil.rmtree(directory)
        self.directories.pop("abort")

    def test_rosinstall_backup_changes(self):
        directory = tempfile.mkdtemp()
        self.directories["backup"] = directory
        cmd = self.rosinstall_fn
        cmd.extend([directory, os.path.join(roslib.packages.get_pkg_dir("test_rosinstall"), "rosinstalls", "simple.rosinstall"), "-n"])
        self.assertEqual(0,subprocess.call(cmd))

        directory1 = tempfile.mkdtemp()
        self.directories["backup1"] = directory1
        cmd.extend([directory, os.path.join(roslib.packages.get_pkg_dir("test_rosinstall"), "rosinstalls", "simple_changed_uri.rosinstall"), "--backup-changed-uri=%s"%directory1, "-n"])
        self.assertEqual(0,subprocess.call(cmd))

        self.assertEqual(len(os.listdir(directory1)), 1)

        shutil.rmtree(directory)
        self.directories.pop("backup")
        shutil.rmtree(directory1)
        self.directories.pop("backup1")


if __name__ == '__main__':
    rostest.unitrun('test_rosinstall', 'test_commandline', RosinstallOptionsTest, coverage_packages=['rosinstall'])  
    sys.exit(0)
    rostest.unitrun('test_rosinstall', 'test_commandline', RosinstallCommandlineTest, coverage_packages=['rosinstall'])  
    rostest.unitrun('test_rosinstall', 'test_commandline_overlay', RosinstallCommandlineOverlays, coverage_packages=['rosinstall'])  

