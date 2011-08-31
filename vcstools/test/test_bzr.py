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

import os
import sys
import unittest
import subprocess
import tempfile
import shutil

class BZRClientTest(unittest.TestCase):

    def setUp(self):
        from vcstools.bzr import BzrClient
        
        directory = tempfile.mkdtemp()
        self.directories = dict(setUp=directory)
        remote_path = os.path.join(directory, "remote")
        os.makedirs(remote_path)

        # create a "remote" repo
        subprocess.check_call(["bzr", "init"], cwd=remote_path)
        subprocess.check_call(["touch", "fixed.txt"], cwd=remote_path)
        subprocess.check_call(["bzr", "add", "fixed.txt"], cwd=remote_path)
        subprocess.check_call(["bzr", "commit", "-m", "initial"], cwd=remote_path)
        subprocess.check_call(["bzr", "tag", "test_tag"], cwd=remote_path)
        self.readonly_version_init = "1"
        
        # files to be modified in "local" repo
        subprocess.check_call(["touch", "modified.txt"], cwd=remote_path)
        subprocess.check_call(["touch", "modified-fs.txt"], cwd=remote_path)
        subprocess.check_call(["bzr", "add", "modified.txt", "modified-fs.txt"], cwd=remote_path)
        subprocess.check_call(["bzr", "commit", "-m", "initial"], cwd=remote_path)
        self.readonly_version_second = "2"
        
        subprocess.check_call(["touch", "deleted.txt"], cwd=remote_path)
        subprocess.check_call(["touch", "deleted-fs.txt"], cwd=remote_path)
        subprocess.check_call(["bzr", "add", "deleted.txt", "deleted-fs.txt"], cwd=remote_path)
        subprocess.check_call(["bzr", "commit", "-m", "modified"], cwd=remote_path)
        self.readonly_version = "3"

        self.readonly_path = os.path.join(directory, "readonly")
        self.readonly_url = remote_path
        
        client = BzrClient(self.readonly_path)
        self.assertTrue(client.checkout(self.readonly_url, self.readonly_version))

    def tearDown(self):
        for d in self.directories:
            shutil.rmtree(self.directories[d])

    def test_get_url_by_reading(self):
        from vcstools.bzr import BzrClient
        client = BzrClient(self.readonly_path)
        self.assertTrue(client.path_exists())
        self.assertTrue(client.detect_presence())
        self.assertEqual(client.get_url(), self.readonly_url)
        self.assertEqual(client.get_version(), self.readonly_version)

    def test_get_type_name(self):
        from vcstools.bzr import BzrClient
        local_path = "/tmp/dummy"
        client = BzrClient(local_path)
        self.assertEqual(client.get_vcs_type_name(), 'bzr')

    def test_checkout(self):
        from vcstools.bzr import BzrClient
        directory = tempfile.mkdtemp()
        self.directories["checkout_test"] = directory
        local_path = os.path.join(directory, "ros")
        url = self.readonly_url
        client = BzrClient(local_path)
        self.assertFalse(client.path_exists())
        self.assertFalse(client.detect_presence())
        self.assertFalse(client.detect_presence())
        self.assertTrue(client.checkout(url))
        self.assertTrue(client.path_exists())
        self.assertTrue(client.detect_presence())
        self.assertEqual(client.get_path(), local_path)
        self.assertEqual(client.get_url(), url)

        #self.assertEqual(client.get_version(), '-r*')
        shutil.rmtree(directory)
        self.directories.pop("checkout_test")

    def test_checkout_specific_version_and_update(self):
        from vcstools.bzr import BzrClient
        directory = tempfile.mkdtemp()
        subdir = "checkout_specific_version_test"
        self.directories[subdir] = directory
        local_path = os.path.join(directory, "ros")
        url = self.readonly_url
        version = "1"
        client = BzrClient(local_path)
        self.assertFalse(client.path_exists())
        self.assertFalse(client.detect_presence())
        self.assertFalse(client.detect_presence())
        self.assertTrue(client.checkout(url, version))
        self.assertTrue(client.path_exists())
        self.assertTrue(client.detect_presence())
        self.assertEqual(client.get_path(), local_path)
        self.assertEqual(client.get_url(), url)
        self.assertEqual(client.get_version(), version)
        
        new_version = '2'
        self.assertTrue(client.update(new_version))
        self.assertEqual(client.get_version(), new_version)
        
        shutil.rmtree(directory)
        self.directories.pop(subdir)
