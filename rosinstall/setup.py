
from distutils.core import setup

setup(name='rosinstall',
      version='0.5.13',
      packages=['rosinstall', 'rosinstall.vcs'],
      package_dir = {'':'src'},
      scripts = ["scripts/rosinstall"],
      author = "Tully Foote", 
      author_email = "tfoote@willowgarage.com",
      url = "http://www.ros.org/wiki/rosinstall",
      download_url = "http://pr.willowgarage.com/downloads/rosinstall/", 
      keywords = ["ROS"],
      classifiers = [
        "Programming Language :: Python", 
        "License :: OSI Approved :: BSD License" ],
      long_description = """\
The installer for ROS
"""
      )
