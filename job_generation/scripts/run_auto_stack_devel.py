#!/usr/bin/python

from roslib import distro, stack_manifest
from run_auto_stack_common import *
import sys
import re
import os
import urllib2
import optparse 
import subprocess
    

def main():
    # parse command line options
    parser = optparse.OptionParser()
    
    parser.add_option('--stack', dest = 'stack', default=False, action='store',
                      help='Stack name')
    parser.add_option('--rosdistro', dest = 'rosdistro', default=False, action='store',
                      help='Ros distro name')
    (options, args) = parser.parse_args()
    if not options.stack or not options.rosdistro:
        print 'You did not specify all options to run this script.'
        return


    # set environment
    ENV = {}
    ENV['PYTHONPATH'] = '/opt/ros/%s/ros/core/roslib/src'%options.rosdistro
    ENV['WORKSPACE'] = os.environ['WORKSPACE']
    ENV['INSTALL_DIR'] = os.environ['INSTALL_DIR']
    ENV['HOME'] = os.environ['INSTALL_DIR']
    ENV['JOB_NAME'] = os.environ['JOB_NAME']
    ENV['BUILD_NUMBER'] = os.environ['BUILD_NUMBER']
    ENV['ROS_TEST_RESULTS_DIR'] = os.environ['ROS_TEST_RESULTS_DIR']
    ENV['PWD'] = os.environ['WORKSPACE']
    ENV['ROS_PACKAGE_PATH'] = '%s:/opt/ros/%s/stacks'%(os.environ['WORKSPACE'], options.rosdistro)
    ENV['ROS_ROOT'] = '/opt/ros/%s/ros'%options.rosdistro
    ENV['PATH'] = '/opt/ros/%s/ros/bin:%s'%(options.rosdistro, os.environ['PATH'])


    # Parse distro file
    rosdistro_obj = distro.Distro(ROSDISTRO_MAP[options.rosdistro])
    print 'Operating on ROS distro %s'%rosdistro_obj.release_name


    # Install Debian packages of stack dependencies
    stack_xml = rosdistro_obj.stacks[options.stack].dev_svn + '/stack.xml'
    stack_file = urllib2.urlopen(stack_xml)
    depends = stack_manifest.parse(stack_file.read()).depends
    stack_file.close()
    print 'Installing stack dependencies Debians: %s'%stacks_to_debs(depends, options.rosdistro)
    res, err = subprocess.Popen('sudo apt-get update'.split(' '),
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=ENV).communicate()
    print res
    res, err = subprocess.Popen(('sudo apt-get install %s %s --yes'%(stack_to_deb(options.stack, options.rosdistro), 
                                                                     stacks_to_debs(depends, options.rosdistro))).split(' '),
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=ENV).communicate()
    print res
    

    # Install system dependencies
    print 'Installing system dependencies'
    res, err = subprocess.Popen(('rosdep install %s -y'%options.stack).split(' '),
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=ENV).communicate()
    print res


    # Start Hudson Helper
    print 'Running Hudson Helper'
    res, err = subprocess.Popen(('python hudson_helper --dir-test %s build'%options.stack).split(' '),
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=ENV).communicate()
    print res


if __name__ == '__main__':
    main()



