#!/usr/bin/env python

import subprocess
import os, sys
import time
import shutil
import tempfile
import optparse
import traceback
import urllib

#ROSBUILD_SSH_URI = 'https://home.willowgarage.com/wgwiki/Servers/hudson?action=AttachFile&do=get&target=rosbuild-ssh.tar'
ROSBUILD_SSH_URI = 'http://wgs24.willowgarage.com/hudson_slave_configuration_files/rosbuild-ssh.tar'

# Valid options
valid_archs = ['i386', 'i686', 'amd64']
valid_ubuntu_distros = ['hardy', 'jaunty', 'karmic', 'lucid', 'maverick']
valid_debian_distros = ['lenny']


def get_mount_points(pattern = "chroot"):
    mnt = subprocess.Popen("mount", stdout=subprocess.PIPE)
    out = mnt.communicate()[0]
    lines = out.split('\n')
    mounts = []
    for l in lines:
        if pattern in l:
            elements = l.split()
            if len(elements) == 6:
                mount_point = elements[2]
                # TODO use os.path.ismount to verify
                mounts.append(mount_point)
    return mounts

def get_chroot_processes(patterns):
    mnt = subprocess.Popen(["sudo", "lsof"], stdout=subprocess.PIPE)
    out = mnt.communicate()[0]
    lines = out.split('\n')
    processes = set()
    for l in lines:
        for p in patterns:
            if p in l:
                elements = l.split()
                if len(elements) > 6:
                    process = elements[1]
                    processes.add(process)
    return processes


def unmount_directories(mounts):
    for m in mounts:
        print "Unmounting %s:"%m
        cmd = "sudo umount -f %s"%m
        subprocess.call(cmd.split())

def kill_processes(processes, level=''):
    for p in processes:
        print "Killing %s %s:"%(level, p)
        cmd = "sudo kill %s %s"%(level, p)
        subprocess.call(cmd.split())

def add_binfmg_misc_mounts(mounts):
    """
    binfmg_misc gets mounted inside the chroot and prevents cleanup
    add this for all proc mounts at the top.  
    """

    additions = [os.path.join(m, 'sys', 'fs', 'binfmt_misc') for m in mounts if m.endswith('proc')]
    print "adding", additions
    return additions + mounts

def clean_up_chroots():
    ### Try 1
    mounts = get_mount_points()
    mounts.reverse()
    if len(mounts) > 0:
        print "Cleaning up mount points", mounts
    else:
        print "No mounts need cleaning" 
        return True

    mounted_processes = get_chroot_processes(mounts)
    for p in mounted_processes:
        print "the following processes are in chroot", p
    kill_processes(mounted_processes)

    remaining_processes = get_chroot_processes(mounts)
    print "Remaining processes %s"%remaining_processes

    mounts = add_binfmg_misc_mounts(mounts)
    unmount_directories(mounts)


    mounts = get_mount_points()
    mounts.reverse()
    # test for success
    if len(remaining_processes) == 0 and len(mounts) == 0:
        return True
    print "Escalating to -9 kills"

    remaining_processes = get_chroot_processes(mounts)
    print "Remaining processes %s"%remaining_processes


    kill_processes(remaining_processes, '-9')

    mounts = add_binfmg_misc_mounts(mounts)
    unmount_directories(mounts)


    remaining_processes = get_chroot_processes(mounts)
    mounts = get_mount_points()
    if len(remaining_processes) == 0 and len(mounts) == 0:
        return True
    return False


def execute_chroot(cmd, path, user='root'):
    if user == 'root':
        full_cmd = ["sudo", "chroot", path]
        full_cmd.extend(cmd)
    else:
        envs = []
        #hudson_envs = ["BUILD_NUMBER", 'BUILD_ID', 'JOB_NAME', 'BUILD_TAG', 'EXECUTOR_NUMBER', 'WORKSPACE', 'HUDSON_URL', 'BUILD_URL', 'JOB_URL', 'SVN_REVISION', 'CVS_BRANCH']
        hudson_envs = ["BUILD_NUMBER", 'BUILD_ID', 'JOB_NAME', 'BUILD_TAG', 'EXECUTOR_NUMBER', 'HUDSON_URL', 'BUILD_URL', 'JOB_URL', 'SVN_REVISION']
        for k,v in os.environ.copy().iteritems():
            if k in hudson_envs:
                envs.append("%s='%s'"%(k, v))
        full_cmd = ['sudo', 'chroot', path, 'su', user, '-s', '/bin/bash',  '-c', '%s %s'%(" ".join(envs), " ".join(cmd))]
    print "Executing", full_cmd
    subprocess.check_call(full_cmd)




class ChrootInstance:
    def __init__(self, distro, arch, path, host_workspace, clear_chroot = True, ssh_key_path = None, use_wg_sources = False, scratch_dir=None, hdd_tmp_dir=None):
        #logging
        self.profile = []
        self.chroot_path = path
        self.host_workspace = host_workspace
        self.mount_path = "/tmp/workspace"
        self.ccache_dir = "/tmp/ccache"
        self.host_ccache_dir = "~/.ccache"
        self.ccache_remote_dir = os.path.join(self.chroot_path, self.ccache_dir[1:])
        self.ws_remote_path = os.path.join(self.chroot_path, self.mount_path[1:])
        self.failure = False
        self.arch = arch
        self.distro = distro
        self.clear_chroot = clear_chroot
        self.workspace_successfully_copied = False
        self.ssh_key_path = ssh_key_path
        self.use_wg_sources = use_wg_sources
        self.hdd_tmp_dir = hdd_tmp_dir
        self.scratch_dir = scratch_dir


    def clean(self):
        self.unmount_proc_sys()

        # clear chroot if it exists
        print "Removing tree %s"%self.chroot_path
        #shutil.rmtree(self.chroot_path, True)
        cmd = ["sudo", "rm", "-rf", self.chroot_path]
        print "executing", cmd
        subprocess.call(cmd)

    def unmount_proc_sys(self):
        cmd = ['sudo', 'umount', '-f',  "%s/proc"%self.chroot_path]
        print cmd
        subprocess.call(cmd)
        cmd = ['sudo', 'umount', '-f', "%s/sys"%self.chroot_path]
        print cmd
        subprocess.call(cmd)

    def mount_proc_sys(self):
        #hack since we mount it in 2 places and umount is safe
        print "unmounting before mounting to prevent double mounting"
        self.unmount_proc_sys()

        cmd = ['sudo', 'mount', '--bind', "/proc", "%s/proc"%self.chroot_path]
        print cmd
        subprocess.call(cmd)
        cmd = ['sudo', 'mount', '--bind', "/sys", "%s/sys"%self.chroot_path]
        print cmd
        subprocess.call(cmd)

    def bootstrap(self):
        cmd = ['sudo', 'apt-get', 'install', 'debootstrap']
        print cmd
        subprocess.check_call(cmd)
        
        deboot_url = 'http://aptproxy.willowgarage.com/us.archive.ubuntu.com/ubuntu'
        if self.distro in valid_debian_distros:
            deboot_url = 'http://ftp.us.debian.org/debian/'

        cmd = ['sudo', 'debootstrap', '--arch', self.arch, self.distro, self.chroot_path, deboot_url]
        print cmd
        subprocess.check_call(cmd)
        print "Finished debootstrap"


        # replicate host settings
        cmd = ['sudo', 'cp', '/etc/resolv.conf', os.path.join(self.chroot_path, 'etc')]
        print "Runing cmd", cmd
        subprocess.check_call(cmd)
        cmd = ['sudo', 'cp', '/etc/hosts', os.path.join(self.chroot_path, 'etc')]
        print "Runing cmd", cmd
        subprocess.check_call(cmd)

        # Move sources.list to apt-proxy
        sources=os.path.join(self.chroot_path, 'etc', 'apt', 'sources.list.d', 'aptproxy.list')

        with tempfile.NamedTemporaryFile() as tf:
            print "Setting sources to aptproxy.willowgarage.com", sources
            tf.write("deb http://aptproxy.willowgarage.com/us.archive.ubuntu.com/ubuntu %s main restricted universe multiverse\n" % self.distro)
            tf.write("deb http://aptproxy.willowgarage.com/us.archive.ubuntu.com/ubuntu %s-updates main restricted universe multiverse\n" % self.distro)
            tf.write("deb http://aptproxy.willowgarage.com/us.archive.ubuntu.com/ubuntu %s-security main restricted universe multiverse\n" % self.distro)

            tf.flush()
            cmd = ['sudo', 'cp', tf.name, sources]
            print "Runing cmd", cmd
            subprocess.check_call(cmd)

        
        self.add_ros_sources()

        # This extra source is to pull in the very latest
        # nvidia-current package from our mirror.  It's only guaranteed
        # to be available for Lucid, but we only need it for Lucid.
        if self.use_wg_sources:
            self.add_wg_sources()

        #disable start-stop-daemon and invokerc

        with tempfile.NamedTemporaryFile() as tf:
            tf.write("#!/bin/sh\n")
            tf.write("exit 0\n")
            tf.flush()
            
            startstop=os.path.join(self.chroot_path,'sbin/start-stop-daemon')
            print "disabling start-stop", startstop
            subprocess.check_call(['sudo', 'cp', tf.name, startstop])
            
            invokerc=os.path.join(self.chroot_path,'usr/sbin/invoke-rc.d')
            print "disabling start-stop", invokerc
            subprocess.check_call(['sudo', 'cp', tf.name, invokerc])


        self.mount_proc_sys()

        if self.distro in valid_ubuntu_distros:
            self.execute(['locale-gen', 'en_US.UTF-8'])

        self.execute(['apt-get', 'update'])


          # Fix the sudoers file
        sudoers_path = os.path.join(self.chroot_path, 'etc/sudoers')
        subprocess.check_call(['sudo', 'chown', '0.0', sudoers_path])

        print "debconf executing"
        chrootcmd = ['sudo', 'chroot', self.chroot_path]
        subprocess.Popen(chrootcmd + ['debconf-set-selections'], stdin=subprocess.PIPE).communicate("""
  hddtemp hddtemp/port string 7634
  hddtemp hddtemp/interface string 127.0.0.1
  hddtemp hddtemp/daemon boolean false
  hddtemp hddtemp/syslog string 0
  hddtemp hddtemp/SUID_bit boolean false
  sun-java6-bin shared/accepted-sun-dlj-v1-1 boolean true
  sun-java6-jdk shared/accepted-sun-dlj-v1-1 boolean true
  sun-java6-jre shared/accepted-sun-dlj-v1-1 boolean true
  grub-pc grub2/linux_cmdline string
  grub-pc grub-pc/install_devices_empty boolean true
  """);
        print "debconf complete"


        # If we're on lucid, pull in the nvidia drivers, in case we're
        # going to run Gazebo-based tests, which need the GPU.
        if self.distro == 'lucid':
            # The --force-yes is necessary to accept the nvidia-current
            # package without a valid GPG signature.
            self.execute(['apt-get', 'install', '-y', '--force-yes', 'nvidia-current'])
            self.execute(['mknod', '/dev/nvidia0', 'c', '195', '0'])
            self.execute(['mknod', '/dev/nvidiactl', 'c', '195', '255'])
            self.execute(['chmod', '666', '/dev/nvidia0', '/dev/nvidiactl'])

        cmd = ("sudo tee -a %s"%sudoers_path).split()
        print "making rosbuild have no passwd", cmd
        tempf = tempfile.TemporaryFile()
        tempf.write("rosbuild ALL = NOPASSWD: ALL\n")
        tempf.seek(0)
        subprocess.check_call(cmd, stdin = tempf)


        #fix sudo permissions
        self.execute(['chown', '-R', 'root:root', '/usr/bin/sudo'])
        self.execute(['chmod', '4755', '-R', '/usr/bin/sudo'])


        cmd = "useradd rosbuild -m --groups sudo".split()
        print self.execute(cmd)

        self.setup_ssh_client()

    def add_ros_sources(self):
        """
        Add code.ros.org sources to the apt sources
        """
        ros_source=os.path.join(self.chroot_path, 'etc', 'apt', 'sources.list.d', 'ros-latest.list')
        with tempfile.NamedTemporaryFile() as tf:
            print "Adding code.ros.org as source"
            #tf.write("deb http://code.ros.org/packages/ros/ubuntu %s main\n" % self.distro)
            tf.write("deb http://code.ros.org/packages/ros-shadow-fixed/ubuntu %s main\n" % self.distro)
            tf.flush()
            cmd = ['sudo', 'cp', tf.name, ros_source]
            print "Runing cmd", cmd
            subprocess.check_call(cmd)

            
        print "adding code.ros.org gpg key"
        key_file = 'tmp/ros.key'
        abs_key_file =os.path.join(self.chroot_path, key_file)
        urllib.urlretrieve('http://code.ros.org/packages/ros.key', abs_key_file)
        #with open(abs_key_file) as f:
        #    print "key file:", f.read()
        cmd = ['apt-key', 'add', os.path.join('/', key_file)]
        self.execute(cmd) 

    def add_wg_sources(self):
        """ 
        Add wg-packages to apt sources for nvidia-current drivers.   
        """
        nvidia_source=os.path.join(self.chroot_path, 'etc', 'apt', 'sources.list.d', 'wg.list')
        with tempfile.NamedTemporaryFile() as tf:
            print "Adding code.ros.org as source"
            tf.write("deb http://wgs1.willowgarage.com/wg-packages/ %s-wg main\n" % self.distro)
            tf.flush()
            cmd = ['sudo', 'cp', tf.name, nvidia_source]
            print "Runing cmd", cmd
            subprocess.check_call(cmd)

            
        print "adding wg gpg key"
        key_file = 'tmp/wg.key'
        abs_key_file =os.path.join(self.chroot_path, key_file)
        urllib.urlretrieve('http://wgs1.willowgarage.com/wg-packages/wg.key', abs_key_file)
        
        #with open(abs_key_file) as f:
        #    print "key file:", f.read()
        cmd = ['apt-key', 'add', os.path.join('/', key_file)]
        self.execute(cmd) 

    def setup_ssh_client(self):
        print 'Setting up ssh client'
        # Pull in ssh, and drop a private key that will allow the slave to
        # upload results of the build.
        self.execute(['apt-get', 'install', '-y', '--force-yes', 'openssh-client'])
        # Pull down a tarball of rosbuild's .ssh directory
        tardestdir = os.path.join(self.chroot_path, 'home', 'rosbuild',)
        #tardestname = os.path.join(tardestdir, 'rosbuild-ssh.tar')
        #if not os.path.exists(tardestname):
        local_tmp_dir = tempfile.mkdtemp()
        local_tmp = os.path.join(local_tmp_dir, "rosbuild_ssh.tar.gz")
        if self.ssh_key_path:
            print "retrieving %s to %s"%(self.ssh_key_path, local_tmp)
            shutil.copy(self.ssh_key_path, local_tmp)
        else:
            print "retrieving %s to %s"%(ROSBUILD_SSH_URI, local_tmp)
            urllib.urlretrieve(ROSBUILD_SSH_URI, local_tmp)
            
        if not os.path.exists(tardestdir):
            os.makedirs(tardestdir)
        print "untarring %s"%local_tmp
        subprocess.check_call(['sudo', 'tar', 'xf', local_tmp], cwd=tardestdir)
        #subprocess.check_call(['sudo', 'rm', '-rf', local_tmp_dir])
        shutil.rmtree(local_tmp_dir)

        #self.execute(['tar', 'xf', os.path.join('home', 'rosbuild', 'rosbuild-ssh.tar')], cwd=os.path.join('home', 'rosbuild'))
        self.execute(['chown', '-R', 'rosbuild:rosbuild', '/home/rosbuild'])

    def replecate_workspace(self):
        print "Linking in workspace"
        subprocess.check_call(["sudo", "mkdir", "-p", self.ws_remote_path]);
        # backwards compatability /tmp/ros
        subprocess.check_call(["sudo", "mkdir", "-p", os.path.join(self.ws_remote_path, "../ros")]);
        subprocess.check_call(['sudo', 'mount', '--bind', self.host_workspace, self.ws_remote_path])
        #backwards compatability /tmp/ros
        subprocess.check_call(['sudo', 'mount', '--bind', self.host_workspace, os.path.join(self.ws_remote_path, "../ros")])        
        cmd = ['chown', '-R', 'rosbuild:rosbuild', self.mount_path]
        self.execute(cmd)

        if self.scratch_dir:
            self.temp_hdd_dir = tempfile.mkdtemp(dir=self.hdd_tmp_dir)
            self.hdd_remote_mount = os.path.join(self.chroot_path, self.scratch_dir.lstrip('/'))
            print "created tempdir", self.temp_hdd_dir
            subprocess.check_call(['sudo', 'mkdir', '-p', self.hdd_remote_mount])
            subprocess.check_call(['sudo', 'mount', '--bind', self.temp_hdd_dir, self.hdd_remote_mount])
            print "mounting tempdir to %s"%os.path.join(self.chroot_path, self.scratch_dir)


    def write_back_workspace(self):
        
        print "unmounting workspace"
        subprocess.call(['sudo', 'umount', '-f', self.ws_remote_path])
        #backwards compatability /tmp/ros
        subprocess.call(['sudo', 'umount', '-f', os.path.join(self.ws_remote_path, "../ros")])       

        print "Cleaning up permissions on workspace."
        subprocess.call(['sudo', 'chown', '-R', '%d:%d'%(os.geteuid(), os.geteuid()), self.host_workspace])

        
        if self.scratch_dir:
            print "Cleaning up scratch mount %s"%self.hdd_remote_mount
            subprocess.call(['sudo', 'umount', '-f', self.hdd_remote_mount])
            print "deleting tempdir", self.hdd_tmp_dir
            shutil.rmtree(self.temp_hdd_dir)

    def manual_init(self):
        

        print "Starting init"
        if self.clear_chroot and os.path.isdir(self.chroot_path):
            print"Clean build requested and directory exists cleaning up old path first." 
            self.clean()
            self.bootstrap()
        elif not os.path.isdir(self.chroot_path):
            self.bootstrap() # bootstrap if cleaned or uninitialized
            print "finished bootstrap"
        else:
            print "configuring"
            self.execute(['dpkg', '--configure', '-a']) # clean up in case dpkg was previously interrupted

        # Even if we're reusing the chroot, we re-mount /proc and /sys.
        self.mount_proc_sys()

        # We setup ~rosbuild/.ssh every time.  It
        # should only be done during the bootstrap step, but it was added
        # after a great many chroot were already bootstrapped, are being 
        # reused.  Also, the server key sometimes changes and so the
        # contents of ~rosbuild/.ssh need to be updated.
        self.setup_ssh_client()



        
        self.replecate_workspace()


    

    def __enter__(self):
        return self
    def __exit__(self, mtype, value, tb):
        if tb:
            if isinstance(value, subprocess.CalledProcessError):
                print "Command failed, shutting down chroot"
            else:
                print "Exception in chroot, shutting down chroot"
            
        self.shutdown()

    def print_profile(self):
        print "chroot Profile:"
        total_time = 0
        for line in self.profile:
            print " %.1f: %s"%(line[0], line[1])
            total_time += line[0]
        print "Total Time: %f"%(total_time)



    def shutdown(self):
        print "Shutting down"
        self.unmount_proc_sys()
        self.write_back_workspace()

    def execute(self, cmd, robust = False, user='root'):
        start_time = time.time()
        if robust:
            try:
                execute_chroot(cmd, self.chroot_path, user)
            except subprocess.CalledProcessError, ex:
                pass
        else:
            execute_chroot(cmd, self.chroot_path, user)
        net_time = time.time() - start_time
        self.profile.append((net_time, "executed: %s"%cmd))

def run_chroot(options, path, workspace, hdd_tmp_dir):
    with ChrootInstance(options.distro, options.arch, path, workspace, clear_chroot = not options.persist, ssh_key_path=options.ssh_key_path, use_wg_sources = options.use_wg_sources, scratch_dir = options.hdd_scratch, hdd_tmp_dir=hdd_tmp_dir) as chrti:

        #initialization here so that if it throws the cleanup is called.  
        chrti.manual_init()

        cmd = "apt-get update".split()
        chrti.execute(cmd)

        cmd = "apt-get install -y --force-yes build-essential python-yaml cmake subversion mercurial wget python-setuptools".split()
        chrti.execute(cmd)

        cmd = "sudo easy_install -U rosinstall".split()
        chrti.execute(cmd)

        if options.arch in ['i386', 'i686']:

          setarch = 'setarch %s'%(options.arch)
        else:
          setarch = ''


        if options.script:
            remote_script_name = os.path.join("/tmp", os.path.basename(options.script))
            cmd = ["sudo", "cp", options.script, os.path.join(chrti.chroot_path, "tmp")]
            print "Executing", cmd
            subprocess.check_call(cmd);
            cmd = ("chown rosbuild:rosbuild %s"%remote_script_name).split()
            chrti.execute(cmd)
            cmd = ("chmod +x %s"%remote_script_name).split()
            chrti.execute(cmd)
            cmd = [remote_script_name]
            if options.arch in ['i386', 'i686']:
                cmd.insert(0, options.arch)
                cmd.insert(0, "setarch")
            chrti.execute(cmd, user="rosbuild")
            
        else:
            cmd = ("wget http://code.ros.org/svn/ros/installers/trunk/hudson/hudson_helper --no-check-certificate -O %s/hudson_helper"%(chrti.mount_path)).split()
            chrti.execute(cmd, user='rosbuild')


            cmd = ("chmod +x %s/hudson_helper"%chrti.mount_path).split()
            chrti.execute(cmd, user='rosbuild')


            cmd = ("chown rosbuild:rosbuild %s"%chrti.mount_path).split() # if 
            print chrti.execute(cmd)

            cmd = ["bash", "-c", "export PATH=/usr/lib/ccache:$PATH && export CCACHE_DIR=%s &&export JOB_NAME=%s && export BUILD_NUMBER=%s && export HUDSON_URL=%s && export WORKSPACE=/tmp/ros && cd %s && %s %s/hudson_helper %s"%(chrti.ccache_dir, os.getenv('JOB_NAME'), os.getenv('BUILD_NUMBER'), os.getenv('HUDSON_URL'), chrti.mount_path, setarch, chrti.mount_path, options.hudson_args)]
            chrti.execute(cmd, user='rosbuild')

        print chrti.print_profile()


        
class TempRamFS:
    def __init__(self, path, size_str):
        self.path = path
        self.size= size_str
        
    def __enter__(self):
        
        cmd = ['sudo', 'mkdir', '-p', self.path]
        subprocess.check_call(cmd)
        cmd = ['sudo', 'mount', '-t', 'tmpfs', '-o', 'size=%s,mode=0755'%self.size, 'tmpfs', self.path]
        subprocess.check_call(cmd)
        return self

    def __exit__(self, mtype, value, tb):
        if tb:
            if isinstance(value, subprocess.CalledProcessError):
                print >> sys.stderr, "Command failed, closing out ramdisk"
            else:
                print >> sys.stderr, "Caught exception, closing out ramdisk"
            
        cmd = ['sudo', 'umount', '-f', self.path]
        if not subprocess.call(cmd):
            print "WARNING: UNCLEAN TMPFS CHROOT UNMONT"
        else:
            print "Successfully umounted tmpfs chroot."



workspace = os.getenv("WORKSPACE")
if not workspace:
    print "you must export WORKSPACE"
    sys.exit(1)

hdd_tmp_dir = os.getenv("HDD_TMP_DIR", "/tmp")




parser = optparse.OptionParser()
parser.add_option("--hudson", type="string", dest="hudson_args", 
                  help="args to pass through to hudson_helper") 
parser.add_option("--arch", type="string", dest="arch",
                  help="What architecture %s"%valid_archs)
parser.add_option("--distro", type="string", dest="distro",
                  help="What distro %s "%(valid_ubuntu_distros + valid_debian_distros))
parser.add_option("--persist-chroot", action="store_true", dest="persist", default=False,
                  help="do not clear the chroot before running")
parser.add_option("--chroot-dir", action="store", dest="chroot_dir", default="/home/rosbuild/chroot",
                  type="string", help="prefix for ros_release")
parser.add_option("--ramdisk-size", action="store", dest="ramdisk_size", default="20000M",
                  type="string", help="Ramdisk size string, default '20GB'")
parser.add_option("--ramdisk", action="store_true", dest="ramdisk", default=False,
                  help="Run chroot in a ramdisk")
parser.add_option("--hdd-scratch", action="store", dest="hdd_scratch", default=False,
                  help="Mount a tempdir on the hdd in this location in the chroot.")
parser.add_option("--use-wg-sources", action="store_true", dest="use_wg_sources", default=False,
                  help="Use internal wg sources.")
parser.add_option("--script", action="store", dest="script",
                  type="string", help="Script filename to execute on the remote machine")
parser.add_option("--ssh-key-file", action="store", dest="ssh_key_path", default=None,
                  type="string", help="filename to use for ssh key tarball, instead of URI")

(options, args) = parser.parse_args()

if not options.script and not options.hudson_args:
    parser.error("hudson_helper needs args")
if options.distro not in (valid_ubuntu_distros + valid_debian_distros):
    parser.error("%s is not a valid distro: %s"%(options.distro, valid_ubuntu_distros+ valid_debian_distros))
if options.arch not in valid_archs:
    parser.error("%s is not a valid arch: %s"%(options.arch, valid_archs))


path = os.path.join(options.chroot_dir, os.getenv("JOB_NAME"))
print "chroot path", path    
print "parameters"
print "hudson_args", options.hudson_args
print "distro", options.distro
print "arch", options.arch
print "workspace", workspace

print "Checking for abandoned chroots"
if not clean_up_chroots():
    print "Failed to clean up abandoned chroots, continuing."

subprocess.check_call(['sudo', 'mkdir', '-p', path])


try:
    if options.ramdisk:
        with TempRamFS(path, options.ramdisk_size):
            cmd = ['mount']
            subprocess.check_call(cmd)
            run_chroot(options, path, workspace, hdd_tmp_dir)

        cmd = ['mount']
        subprocess.check_call(cmd)

    else:
        run_chroot(options, path, workspace, hdd_tmp_dir)

except subprocess.CalledProcessError, e:
    print >> sys.stderr, "Command failed: %s"%(str(e))

sys.exit(0)
