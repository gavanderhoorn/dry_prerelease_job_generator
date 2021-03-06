#!/bin/sh

# We expect the following environment variables to be set:
#export WORKSPACE=`pwd`
#export DISTRO=karmic
#export ARCH=amd64
#export ROSDISTRO=cturtle
#export ROSSTACK=ros
#export ROSVERSION=1.2.0

set -o errexit

export DISTRO_TGZ=${DISTRO}-base.tgz
export DEBNAME=ros-${ROSDISTRO}-`echo $ROSSTACK | sed -e 's/_/-/'`
export DEBVERSION=${ROSVERSION}-0~${DISTRO}
export ROSFILE=${ROSSTACK}-${ROSVERSION}
export DEBFILE=${DEBNAME}_${DEBVERSION}

sudo apt-get install pbuilder
[ -e ${DISTRO_TGZ} ] || 
{
    sudo pbuilder --create --distribution ${DISTRO} --othermirror "deb http://code.ros.org/packages/ros-shadow/ubuntu ${DISTRO} main" --basetgz ${DISTRO_TGZ} --components "main restricted universe multiverse" --extrapackages "wget lsb-release debhelper"
}
mkdir -p download
wget https://code.ros.org/svn/release/download/stacks/${ROSSTACK}/${ROSFILE}/${DEBFILE}.dsc -O download/${DEBFILE}.dsc
wget https://code.ros.org/svn/release/download/stacks/${ROSSTACK}/${ROSFILE}/${DEBFILE}.tar.gz -O download/${DEBFILE}.tar.gz
mkdir -p hookdir
cat > hookdir/A50fetch <<EOF
#!/bin/sh
set -o errexit
wget https://code.ros.org/svn/release/download/stacks/${ROSSTACK}/${ROSFILE}/${ROSFILE}.tar.bz2 -O /tmp/buildd/${ROSFILE}.tar.bz2
EOF
cat > hookdir/D50update <<EOF
#!/bin/sh
set -o errexit
apt-get update
EOF
chmod +x hookdir/A50fetch
chmod +x hookdir/D50update
rm -rf result
mkdir -p result
sudo pbuilder --build --basetgz ${DISTRO_TGZ} --hookdir hookdir  --buildresult result download/${DEBFILE}.dsc
dpkg-scanpackages . /dev/null > result/Packages
cat > script.sh <<EOF
#!/bin/sh
set -o errexit
echo "deb file:/home/leibs/workspace result/" > /etc/apt/sources.list.d/pbuild.list
apt-get update
apt-get install ${DEBNAME}=${DEBVERSION} -y --force-yes
dpkg -l ${DEBNAME}
EOF
sudo pbuilder --execute --basetgz ${DISTRO_TGZ} --bindmounts /home/leibs/workspace/result script.sh