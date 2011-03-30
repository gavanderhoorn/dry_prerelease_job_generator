#!/usr/bin/python

STACK_DIR = 'stack_overlay'
DEPENDS_DIR = 'depends_overlay'
DEPENDS_ON_DIR = 'depends_on_overlay'


import roslib; roslib.load_manifest("job_generation")
from roslib import stack_manifest
import rosdistro
from jobs_common import *
import sys
import os
import optparse 
import subprocess


def main():
    # parse command line options
    (options, args) = get_options(['stack', 'rosdistro'], ['repeat', 'source-only'])
    if not options:
        return -1

    # set environment
    env = get_environment()
    env['ROS_PACKAGE_PATH'] = '%s:%s:%s:/opt/ros/%s/stacks'%(env['INSTALL_DIR']+'/'+STACK_DIR,
                                                             env['INSTALL_DIR']+'/'+DEPENDS_DIR,
                                                             env['INSTALL_DIR']+'/'+DEPENDS_ON_DIR,
                                                             options.rosdistro)
    if 'ros' in options.stack:
        env['ROS_ROOT'] = env['INSTALL_DIR']+'/'+STACK_DIR+'/ros'
        print "We're building ROS, so setting the ROS_ROOT to %s"%(env['ROS_ROOT'])
    else:
        env['ROS_ROOT'] = '/opt/ros/%s/ros'%options.rosdistro
    env['PYTHONPATH'] = env['ROS_ROOT']+'/core/roslib/src'
    env['PATH'] = '/opt/ros/%s/ros/bin:%s'%(options.rosdistro, os.environ['PATH'])


    # Parse distro file
    rosdistro_obj = rosdistro.Distro(get_rosdistro_file(options.rosdistro))
    print 'Operating on ROS distro %s'%rosdistro_obj.release_name


    # Install the stacks to test from source
    print 'Installing the stacks to test from source'
    rosinstall = ''
    for stack in options.stack:
        rosinstall += stack_to_rosinstall(rosdistro_obj.stacks[stack], 'devel')
    rosinstall_file = '%s.rosinstall'%STACK_DIR
    print 'Generating rosinstall file [%s]'%(rosinstall_file)
    print 'Contents:\n\n'+rosinstall+'\n\n'
    with open(rosinstall_file, 'w') as f:
        f.write(rosinstall)
    print 'rosinstall file [%s] generated'%(rosinstall_file)
    call('rosinstall --rosdep-yes %s /opt/ros/%s %s'%(STACK_DIR, options.rosdistro, rosinstall_file), env,
         'Install the stacks to test from source.')


    # get all stack dependencies of stacks we're testing
    depends = []
    for stack in options.stack:    
        stack_xml = '%s/%s/stack.xml'%(STACK_DIR, stack)
        call('ls %s'%stack_xml, env, 'Checking if stack %s contains "stack.xml" file'%stack)
        with open(stack_xml) as stack_file:
            depends_one = [str(d) for d in stack_manifest.parse(stack_file.read()).depends]  # convert to list
            print 'Dependencies of stack %s: %s'%(stack, str(depends_one))
            for d in depends_one:
                if not d in options.stack and not d in depends:
                    print 'Adding dependencies of stack %s'%d
                    get_depends_all(rosdistro_obj, d, depends)
                    print 'Resulting total dependencies: %s'%str(depends)

    if len(depends) > 0:
        if not options.source_only:
            # Install Debian packages  stack dependencies
            print 'Installing debian packages of stack dependencies from stacks %s'%str(options.stack)
            call('sudo apt-get update', env)
            print 'Installing debian packages of "%s" dependencies: %s'%(stack, str(depends))
            call('sudo apt-get install %s --yes'%(stacks_to_debs(depends, options.rosdistro)), env)
        else:
            # Install dependencies from source
            print 'Installing stack dependencies from source'
            if 'ros' in depends:
                depends.remove('ros')
            rosinstall = stacks_to_rosinstall(depends, rosdistro_obj.released_stacks, 'release-tar')
            rosinstall_file = '%s.rosinstall'%DEPENDS_DIR
            with open(rosinstall_file, 'w') as f:
                f.write(rosinstall)
            call('rosinstall --rosdep-yes %s /opt/ros/%s %s'%(DEPENDS_DIR, options.rosdistro, rosinstall_file), env,
                 'Install the stack dependencies from source.')
    else:
        print 'Stack(s) %s do(es) not have any dependencies, not installing anything now'%str(options.stack)

    # Install system dependencies
    print 'Installing system dependencies'
    call('rosmake rosdep', env)
    for stack in options.stack:
        call('rosdep install -y %s'%stack, env,
             'Install system dependencies of stack %s'%stack)

    
    # Run hudson helper for stacks only
    print 'Running Hudson Helper'
    res = 0
    for r in range(0, int(options.repeat)+1):
        env['ROS_TEST_RESULTS_DIR'] = env['ROS_TEST_RESULTS_DIR'] + '/' + STACK_DIR + '_run_' + str(r)
        helper = subprocess.Popen(('./hudson_helper --dir-test %s build'%STACK_DIR).split(' '), env=env)
        helper.communicate()
        if helper.returncode != 0:
            res = helper.returncode
    if res != 0:
        return res


    # Install Debian packages of ALL stacks in distro
    print 'Installing all stacks of ros distro %s: %s'%(options.rosdistro, str(rosdistro_obj.released_stacks.keys()))
    for stack in rosdistro_obj.released_stacks:
        call('sudo apt-get install %s --yes'%(stack_to_deb(stack, options.rosdistro)), env, ignore_fail=True)
    

    # Install all stacks that depend on this stack
    print 'Installing all stacks that depend on these stacks from source'
    depends_on = {}
    for stack in options.stack:
        res = call('rosstack depends-on %s'%stack, env, 'Getting list of stacks that depend on stack %s'%stack)
        if res != '':
            for r in res.split('\n'):
                if r != '':
                    depends_on[r] = ''
    print 'Removing the stacks we are testing from the depends_on list'
    depends_on_keys = list(set(depends_on.keys()) - set(options.stack))
    if len(depends_on_keys) == 0:
        print 'No stacks depends on %s, finishing test.'%options.stack        
        return 0
    print 'These stacks depend on the stacks we are testing: "%s"'%str(depends_on_keys)
    rosinstall = stacks_to_rosinstall(depends_on_keys, rosdistro_obj.released_stacks, 'release-tar')
    rosinstall_file = '%s.rosinstall'%DEPENDS_ON_DIR
    with open(rosinstall_file, 'w') as f:
        f.write(rosinstall)
    call('rosinstall --rosdep-yes %s /opt/ros/%s %s'%(DEPENDS_ON_DIR, options.rosdistro, rosinstall_file), env,
         'Install the stacks that depend on the stacks that are getting tested from source.')

    # Remove stacks that depend on this stack from Debians
    print 'Removing all stacks from Debian that depend on these stacks'
    for stack in options.stack:    
        call('sudo apt-get remove %s --yes'%stack_to_deb(stack, options.rosdistro), env, ignore_fail=True)

    # Run hudson helper for all stacks
    print 'Running Hudson Helper'
    env['ROS_TEST_RESULTS_DIR'] = env['ROS_TEST_RESULTS_DIR'] + '/' + DEPENDS_ON_DIR
    helper = subprocess.Popen(('./hudson_helper --dir-test %s build'%DEPENDS_ON_DIR).split(' '), env=env)
    helper.communicate()
    return helper.returncode


if __name__ == '__main__':
    try:
        res = main()
        sys.exit( res )
    except Exception:
        sys.exit(-1)






