#!/usr/bin/python



# template to create develop hudscon configuration file
HUDSON_DEVEL_CONFIG = """<?xml version='1.0' encoding='UTF-8'?>
<project> 
  <description>Build of STACKNAME development branch for ROSDISTRO on UBUNTUDISTRO, ARCH</description> 
 <logRotator> 
    <daysToKeep>21</daysToKeep> 
    <numToKeep>-1</numToKeep> 
  </logRotator> 
  <keepDependencies>false</keepDependencies> 
  <properties> 
    <hudson.plugins.trac.TracProjectProperty> 
      <tracWebsite>http://code.ros.org/trac/ros/</tracWebsite> 
    </hudson.plugins.trac.TracProjectProperty> 
  </properties> 
  <scm class="hudson.scm.SubversionSCM"> 
    <locations> 
      <hudson.scm.SubversionSCM_-ModuleLocation> 
        <remote>STACKURI</remote> 
        <local>STACKNAME</local> 
      </hudson.scm.SubversionSCM_-ModuleLocation> 
    </locations> 
    <useUpdate>false</useUpdate> 
    <doRevert>false</doRevert> 
    <excludedRegions></excludedRegions> 
    <includedRegions></includedRegions> 
    <excludedUsers></excludedUsers> 
    <excludedRevprop></excludedRevprop> 
    <excludedCommitMessages></excludedCommitMessages> 
  </scm> 
  <assignedNode>hudson-devel</assignedNode>
  <canRoam>false</canRoam> 
  <disabled>false</disabled> 
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding> 
  <triggers class="vector"> 
    <hudson.triggers.SCMTrigger> 
      <spec>TIME_TRIGGER</spec> 
    </hudson.triggers.SCMTrigger> 
  </triggers> 
  <concurrentBuild>false</concurrentBuild> 
  <builders> 
    <hudson.tasks.Shell> 
      <command>cat &gt; $WORKSPACE/script.sh &lt;&lt;DELIM
#!/usr/bin/env bash
set -o errexit
echo "_________________________________BEGIN SCRIPT______________________________________"
export INSTALL_DIR=/tmp/install_dir
export WORKSPACE=/tmp/ros
export ROS_TEST_RESULTS_DIR=/tmp/ros/test_results
export JOB_NAME=$JOB_NAME
export BUILD_NUMBER=$BUILD_NUMBER
export HUDSON_URL=$HUDSON_URL

mkdir -p $INSTALL_DIR
cd $INSTALL_DIR
wget -m -nd http://code.ros.org/svn/ros/installers/trunk/hudson/hudson_helper
wget -m -nd http://code.ros.org/svn/ros/stacks/ros_release/trunk/job_generation/scripts/run_auto_stack_common.py 
wget -m -nd http://code.ros.org/svn/ros/stacks/ros_release/trunk/job_generation/scripts/run_auto_stack_devel.py 

sudo apt-get install ros-ROSDISTRO-ros --yes
source /opt/ros/ROSDISTRO/setup.sh
python run_auto_stack_devel.py --stack STACKNAME --rosdistro ROSDISTRO
echo "_________________________________END SCRIPT_______________________________________"
DELIM

set -o errexit

wget https://code.ros.org/svn/ros/stacks/ros_release/trunk/hudson/scripts/run_chroot.py --no-check-certificate -O $WORKSPACE/run_chroot.py
chmod +x $WORKSPACE/run_chroot.py
cd $WORKSPACE &amp;&amp; $WORKSPACE/run_chroot.py --distro=UBUNTUDISTRO --arch=ARCH  --ramdisk --script=$WORKSPACE/script.sh
     </command> 
    </hudson.tasks.Shell> 
  </builders> 
  <publishers> 
    <hudson.tasks.BuildTrigger> 
      <childProjects>JOB_CHILDREN</childProjects> 
      <threshold> 
        <name>SUCCESS</name> 
        <ordinal>0</ordinal> 
        <color>BLUE</color> 
      </threshold> 
    </hudson.tasks.BuildTrigger> 
    <hudson.tasks.junit.JUnitResultArchiver> 
      <testResults>test_results/_hudson/*.xml</testResults> 
    </hudson.tasks.junit.JUnitResultArchiver> 
    <hudson.plugins.emailext.ExtendedEmailPublisher> 
      <recipientList>EMAIL</recipientList> 
      <configuredTriggers> 
        <hudson.plugins.emailext.plugins.trigger.UnstableTrigger> 
          <email> 
            <recipientList></recipientList> 
            <subject>$PROJECT_DEFAULT_SUBJECT</subject> 
            <body>$PROJECT_DEFAULT_CONTENT</body> 
            <sendToDevelopers>true</sendToDevelopers> 
            <sendToRecipientList>true</sendToRecipientList> 
            <contentTypeHTML>false</contentTypeHTML> 
            <script>true</script> 
          </email> 
        </hudson.plugins.emailext.plugins.trigger.UnstableTrigger> 
        <hudson.plugins.emailext.plugins.trigger.FailureTrigger> 
          <email> 
            <recipientList></recipientList> 
            <subject>$PROJECT_DEFAULT_SUBJECT</subject> 
            <body>$PROJECT_DEFAULT_CONTENT</body> 
            <sendToDevelopers>true</sendToDevelopers> 
            <sendToRecipientList>true</sendToRecipientList> 
            <contentTypeHTML>false</contentTypeHTML> 
            <script>true</script> 
          </email> 
        </hudson.plugins.emailext.plugins.trigger.FailureTrigger> 
        <hudson.plugins.emailext.plugins.trigger.StillFailingTrigger> 
          <email> 
            <recipientList></recipientList> 
            <subject>$PROJECT_DEFAULT_SUBJECT</subject> 
            <body>$PROJECT_DEFAULT_CONTENT</body> 
            <sendToDevelopers>true</sendToDevelopers> 
            <sendToRecipientList>true</sendToRecipientList> 
            <contentTypeHTML>false</contentTypeHTML> 
            <script>true</script> 
          </email> 
        </hudson.plugins.emailext.plugins.trigger.StillFailingTrigger> 
        <hudson.plugins.emailext.plugins.trigger.FixedTrigger> 
          <email> 
            <recipientList></recipientList> 
            <subject>$PROJECT_DEFAULT_SUBJECT</subject> 
            <body>$PROJECT_DEFAULT_CONTENT</body> 
            <sendToDevelopers>true</sendToDevelopers> 
            <sendToRecipientList>true</sendToRecipientList> 
            <contentTypeHTML>false</contentTypeHTML> 
            <script>true</script> 

          </email> 
        </hudson.plugins.emailext.plugins.trigger.FixedTrigger> 
        <hudson.plugins.emailext.plugins.trigger.StillUnstableTrigger> 
          <email> 
            <recipientList></recipientList> 
            <subject>$PROJECT_DEFAULT_SUBJECT</subject> 
            <body>$PROJECT_DEFAULT_CONTENT</body> 
            <sendToDevelopers>true</sendToDevelopers> 
            <sendToRecipientList>true</sendToRecipientList> 
            <contentTypeHTML>false</contentTypeHTML> 
            <script>true</script> 
          </email> 
        </hudson.plugins.emailext.plugins.trigger.StillUnstableTrigger> 
      </configuredTriggers> 
      <defaultSubject>$DEFAULT_SUBJECT</defaultSubject> 
      <defaultContent>$DEFAULT_CONTENT&#xd;
&#xd;
&lt;% &#xd;
def ws = build.getParent().getWorkspace()&#xd;
def computer = build.getExecutor().getOwner()&#xd;
def build_failures = hudson.util.RemotingDiagnostics.executeGroovy(&quot;new File(\&quot;${ws}/build_output/buildfailures.txt\&quot;).text&quot;,computer.getChannel())&#xd;
println &quot;${build_failures}&quot;&#xd;
def test_failures = hudson.util.RemotingDiagnostics.executeGroovy(&quot;new File(\&quot;${ws}/test_output/testfailures.txt\&quot;).text&quot;,computer.getChannel())&#xd;
println &quot;${test_failures}&quot;&#xd;
def build_failures_context = hudson.util.RemotingDiagnostics.executeGroovy(&quot;new File(\&quot;${ws}/build_output/buildfailures-with-context.txt\&quot;).text&quot;,computer.getChannel())&#xd;
println &quot;${build_failures_context}&quot;&#xd;
%&gt;</defaultContent> 
      <defaultContentTypeHTML>false</defaultContentTypeHTML> 
      <defaultContentIsScript>true</defaultContentIsScript> 
    </hudson.plugins.emailext.ExtendedEmailPublisher> 
  </publishers> 
  <buildWrappers/> 
</project>
"""


# template to create pre-release hudson configuration file
HUDSON_PRERELEASE_CONFIG = """<?xml version='1.0' encoding='UTF-8'?>
<project> 
  <description>Pre-release build of STACKNAME for ROSDISTRO on UBUNTUDISTRO, ARCH</description> 
 <logRotator> 
    <daysToKeep>5</daysToKeep> 
    <numToKeep>-1</numToKeep> 
  </logRotator> 
  <keepDependencies>false</keepDependencies> 
  <properties> 
    <hudson.plugins.trac.TracProjectProperty> 
      <tracWebsite>http://code.ros.org/trac/ros/</tracWebsite> 
    </hudson.plugins.trac.TracProjectProperty> 
  </properties> 
  <scm/>
  <assignedNode>hudson-devel</assignedNode>
  <canRoam>false</canRoam> 
  <disabled>false</disabled> 
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding> 
  <authToken>willow</authToken> 
  <triggers class="vector"/> 
  <concurrentBuild>false</concurrentBuild> 
  <builders> 
    <hudson.tasks.Shell> 
      <command>cat &gt; $WORKSPACE/script.sh &lt;&lt;DELIM
#!/usr/bin/env bash
set -o errexit
echo "_________________________________BEGIN SCRIPT______________________________________"
export INSTALL_DIR=/tmp/install_dir
export WORKSPACE=/tmp/ros
export ROS_TEST_RESULTS_DIR=/tmp/ros/test_results
export JOB_NAME=$JOB_NAME
export BUILD_NUMBER=$BUILD_NUMBER
export HUDSON_URL=$HUDSON_URL

mkdir -p $INSTALL_DIR
cd $INSTALL_DIR
wget -m -nd http://code.ros.org/svn/ros/installers/trunk/hudson/hudson_helper 
wget -m -nd http://code.ros.org/svn/ros/stacks/ros_release/trunk/job_generation/scripts/run_auto_stack_common.py 
wget -m -nd http://code.ros.org/svn/ros/stacks/ros_release/trunk/job_generation/scripts/run_auto_stack_prerelease.py 

sudo apt-get install ros-ROSDISTRO-ros --yes
source /opt/ros/ROSDISTRO/setup.sh

python run_auto_stack_prerelease.py --stack STACKNAME --rosdistro ROSDISTRO
echo "_________________________________END SCRIPT_______________________________________"
DELIM

set -o errexit

wget https://code.ros.org/svn/ros/stacks/ros_release/trunk/hudson/scripts/run_chroot.py --no-check-certificate -O $WORKSPACE/run_chroot.py
chmod +x $WORKSPACE/run_chroot.py
cd $WORKSPACE &amp;&amp; $WORKSPACE/run_chroot.py --distro=UBUNTUDISTRO --arch=ARCH  --ramdisk --script=$WORKSPACE/script.sh
     </command> 
    </hudson.tasks.Shell> 
  </builders> 
  <publishers> 
    <hudson.tasks.junit.JUnitResultArchiver> 
      <testResults>test_results/_hudson/*.xml</testResults> 
    </hudson.tasks.junit.JUnitResultArchiver> 
    <hudson.plugins.emailext.ExtendedEmailPublisher> 
      <recipientList>EMAIL</recipientList> 
      <configuredTriggers> 
        <hudson.plugins.emailext.plugins.trigger.UnstableTrigger> 
          <email> 
            <recipientList></recipientList> 
            <subject>$PROJECT_DEFAULT_SUBJECT</subject> 
            <body>$PROJECT_DEFAULT_CONTENT</body> 
            <sendToDevelopers>true</sendToDevelopers> 
            <sendToRecipientList>true</sendToRecipientList> 
            <contentTypeHTML>false</contentTypeHTML> 
            <script>true</script> 
          </email> 
        </hudson.plugins.emailext.plugins.trigger.UnstableTrigger> 
        <hudson.plugins.emailext.plugins.trigger.FailureTrigger> 
          <email> 
            <recipientList></recipientList> 
            <subject>$PROJECT_DEFAULT_SUBJECT</subject> 
            <body>$PROJECT_DEFAULT_CONTENT</body> 
            <sendToDevelopers>true</sendToDevelopers> 
            <sendToRecipientList>true</sendToRecipientList> 
            <contentTypeHTML>false</contentTypeHTML> 
            <script>true</script> 
          </email> 
        </hudson.plugins.emailext.plugins.trigger.FailureTrigger> 
        <hudson.plugins.emailext.plugins.trigger.StillFailingTrigger> 
          <email> 
            <recipientList></recipientList> 
            <subject>$PROJECT_DEFAULT_SUBJECT</subject> 
            <body>$PROJECT_DEFAULT_CONTENT</body> 
            <sendToDevelopers>true</sendToDevelopers> 
            <sendToRecipientList>true</sendToRecipientList> 
            <contentTypeHTML>false</contentTypeHTML> 
            <script>true</script> 
          </email> 
        </hudson.plugins.emailext.plugins.trigger.StillFailingTrigger> 
        <hudson.plugins.emailext.plugins.trigger.FixedTrigger> 
          <email> 
            <recipientList></recipientList> 
            <subject>$PROJECT_DEFAULT_SUBJECT</subject> 
            <body>$PROJECT_DEFAULT_CONTENT</body> 
            <sendToDevelopers>true</sendToDevelopers> 
            <sendToRecipientList>true</sendToRecipientList> 
            <contentTypeHTML>false</contentTypeHTML> 
            <script>true</script> 
          </email> 
        </hudson.plugins.emailext.plugins.trigger.FixedTrigger> 
        <hudson.plugins.emailext.plugins.trigger.StillUnstableTrigger> 
          <email> 
            <recipientList></recipientList> 
            <subject>$PROJECT_DEFAULT_SUBJECT</subject> 
            <body>$PROJECT_DEFAULT_CONTENT</body> 
            <sendToDevelopers>true</sendToDevelopers> 
            <sendToRecipientList>true</sendToRecipientList> 
            <contentTypeHTML>false</contentTypeHTML> 
            <script>true</script> 
          </email> 
        </hudson.plugins.emailext.plugins.trigger.StillUnstableTrigger> 
      </configuredTriggers> 
      <defaultSubject>$DEFAULT_SUBJECT</defaultSubject> 
      <defaultContent>$DEFAULT_CONTENT&#xd;
&#xd;
&lt;% &#xd;
def ws = build.getParent().getWorkspace()&#xd;
def computer = build.getExecutor().getOwner()&#xd;
def build_failures = hudson.util.RemotingDiagnostics.executeGroovy(&quot;new File(\&quot;${ws}/build_output/buildfailures.txt\&quot;).text&quot;,computer.getChannel())&#xd;
println &quot;${build_failures}&quot;&#xd;
def test_failures = hudson.util.RemotingDiagnostics.executeGroovy(&quot;new File(\&quot;${ws}/test_output/testfailures.txt\&quot;).text&quot;,computer.getChannel())&#xd;
println &quot;${test_failures}&quot;&#xd;
def build_failures_context = hudson.util.RemotingDiagnostics.executeGroovy(&quot;new File(\&quot;${ws}/build_output/buildfailures-with-context.txt\&quot;).text&quot;,computer.getChannel())&#xd;
println &quot;${build_failures_context}&quot;&#xd;
%&gt;</defaultContent> 
      <defaultContentTypeHTML>false</defaultContentTypeHTML> 
      <defaultContentIsScript>true</defaultContentIsScript> 
    </hudson.plugins.emailext.ExtendedEmailPublisher> 
  </publishers> 
  <buildWrappers/> 
</project>
"""



# the supported Ubuntu distro's for each ros distro
DEFAULT_ARCHS = ['amd64', 'i386']

# path to hudson server
SERVER = 'http://build.willowgarage.com/'

import roslib; roslib.load_manifest("hudson")
from roslib import distro, rospack, stack_manifest
from job_generation_defines import *
import hudson
import sys
import re
import urllib2
import optparse 

def stack_to_deb(distro_name, stack_name):
    return 'ros-'+distro_name+'-'+(str(stack_name).replace('_','-'))


def devel_job_name(distro_name, stack_name, ubuntu, arch):
    return "_".join(['auto_stack_devel', distro_name, stack_name, ubuntu, arch])

def create_devel_configs(ubuntu_distros, arches, distro_name, stack_name, stack_map, email):
    # create hudson config files for each ubuntu distro
    configs = {}
    for ubuntu in ubuntu_distros:
        for arch in arches:
            name = devel_job_name(distro_name, stack_name, ubuntu, arch)

            # check if this is the 'gold' job
            time_trigger = ''
            job_children = ''
            if arch == DEFAULT_ARCHS[0] and ubuntu == get_ubuntu_distro_map()[distro_name][0]:
                time_trigger = '*/5 * * * *'
                job_children_list = []
                for a in DEFAULT_ARCHS:
                    for u in get_ubuntu_distro_map()[distro_name]:
                        child_name = devel_job_name(distro_name, stack_name, u, a)
                        if child_name != name:
                            job_children_list.append(child_name)
                job_children = ', '.join(job_children_list)

            hudson_config = HUDSON_DEVEL_CONFIG
            hudson_config = hudson_config.replace('UBUNTUDISTRO', ubuntu)
            hudson_config = hudson_config.replace('ARCH', arch)
            hudson_config = hudson_config.replace('ROSDISTRO', distro_name)
            hudson_config = hudson_config.replace('STACKNAME', stack_name)   
            hudson_config = hudson_config.replace('STACKDEB', stack_to_deb(distro_name, stack_name))
            hudson_config = hudson_config.replace('STACKURI', stack_map[stack_name].dev_svn)
            hudson_config = hudson_config.replace('TIME_TRIGGER', time_trigger)
            hudson_config = hudson_config.replace('JOB_CHILDREN', job_children)
            hudson_config = hudson_config.replace('EMAIL', email)
            configs[name] = hudson_config
    return configs


def create_prerelease_configs(ubuntu_distros, arches, distro_name, stack_name, stack_map, email):
    # create hudson config files for each ubuntu distro
    configs = {}
    for ubuntu in ubuntu_distros:
        for arch in arches:
            name = "_".join(['auto_stack_prerelease', distro_name, stack_name, ubuntu, arch])
            hudson_config = HUDSON_PRERELEASE_CONFIG
            hudson_config = hudson_config.replace('UBUNTUDISTRO', ubuntu)
            hudson_config = hudson_config.replace('ARCH', arch)
            hudson_config = hudson_config.replace('ROSDISTRO', distro_name)
            hudson_config = hudson_config.replace('STACKNAME', stack_name)      
            hudson_config = hudson_config.replace('EMAIL', email)
            configs[name] = hudson_config
    return configs
    
    

def main():
    parser = optparse.OptionParser()
    parser.add_option('--delete', dest = 'delete', default=False, action='store_true',
                      help='Delete jobs from Hudson')    
    parser.add_option('--recreate', dest = 'recreate', default=False, action='store_true',
                      help='Re-create jobs instead of updating them')    
    parser.add_option( '--ubuntu', dest = 'ubuntudistro', action='append',
                      help="Specify the Ubuntu distro to create a job for (defaults to all supported Ubuntu distro's")
    parser.add_option('--arch', dest = 'arch', action='append',
                      help="Specify the architectures to operate on (defaults is [i386, amd64]")
    parser.add_option('--stack', dest = 'stacks', action='append',
                      help="Specify the stacks to operate on (defaults to all stacks)")
    parser.add_option('--rosdistro', dest = 'rosdistro', action='store', default='cturtle',
                      help="Specify the ros distro to operate on (defaults to cturtle)")
    parser.add_option('--pre', dest='prerelease', action='store_true', default=False,
                      help='Operate on pre-release scripts')
    parser.add_option('--devel', dest='devel', action='store_true', default=False,
                      help='Operate on devel scripts')
    parser.add_option('--disable', dest='disable', action='store_true', default=False,
                      help='Disable Scripts')
    parser.add_option('--email', dest='email', action='store', default='wim+hudson_auto_stack@willowgarage.com',
                      help='Send email to this address')
    (options, args) = parser.parse_args()

    # Parse distro file
    distro_obj = distro.Distro(get_ros_distro_map()[options.rosdistro])
    print 'Operating on ROS distro %s'%distro_obj.release_name

    # set architctures
    if options.arch:
        archs=options.arch
    else:
        archs = DEFAULT_ARCHS
    print 'Operating on archs %s'%archs
    
    # set ubuntu distro's
    if options.ubuntudistro:
        ubuntudistro=options.ubuntudistro
    else:
        ubuntudistro=get_ubuntu_distro_map()[distro_obj.release_name]
    print 'Operating on Ubuntu distro %s'%ubuntudistro

    # parse username and password
    if len(args) != 2:
        parser.error('Needs username and password as args')
    username = args[0]
    password = args[1]

    # generate hudson config files
    devel_configs = {}
    prerelease_configs = {}
    if options.stacks:
        stack_list = options.stacks
    else:
        stack_list = distro_obj.stacks
    for stack_name in stack_list:
        devel_configs.update(create_devel_configs(ubuntudistro, archs, distro_obj.release_name, stack_name, distro_obj.stacks, options.email))
        prerelease_configs.update(create_prerelease_configs(ubuntudistro, archs , distro_obj.release_name, stack_name, distro_obj.stacks, options.email))
    hudson_instance = hudson.Hudson(SERVER, username, password)


    # send prerelease tests to Hudson
    if options.prerelease:
        for job_name in prerelease_configs:
            exists = hudson_instance.job_exists(job_name)
            if exists:
                if options.delete or options.recreate:
                    hudson_instance.delete_job(job_name)
                    exists = False
                    print "Deleting job %s"%job_name
                elif not options.recreate:
                    hudson_instance.reconfig_job(job_name, prerelease_configs[job_name])
                    print "Reconfigure job %s"%job_name
            if not options.delete and not exists:
                print "Creating new job %s"%job_name
                hudson_instance.create_job(job_name, prerelease_configs[job_name])


    # send devel tests to Hudson
    if options.devel:
        for job_name in devel_configs:
            exists = hudson_instance.job_exists(job_name)
            if exists:
                if options.delete or options.recreate:
                    hudson_instance.delete_job(job_name)
                    exists = False
                    print "Deleting job %s"%job_name
                elif not options.recreate:
                    hudson_instance.reconfig_job(job_name, devel_configs[job_name])
                    if not options.disable: # don't enable if about to disable
                        hudson_instance.enable_job(job_name) # only necessary if disabled, but I don't know how to test if disabled
                    print "Reconfigure job %s"%job_name
                if options.disable:
                    hudson_instance.disable_job(job_name)
            if not options.delete and not options.disable and not exists:
                print "Creating new job %s"%job_name
                hudson_instance.create_job(job_name, devel_configs[job_name])



if __name__ == '__main__':
    main()



