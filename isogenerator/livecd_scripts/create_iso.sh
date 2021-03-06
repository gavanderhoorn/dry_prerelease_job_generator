#!/bin/bash

FILE=$1

if [ "x$FILE" == "x" ] ; then
    echo "You must specifiy a file name for the ISO:"
    echo "$0 <file-name>"
    exit 1
fi

echo "Creating new ISO $FILE"

echo "Remove any preexisting iso"
rm -f $FILE

echo "Recreate manifest"
chmod +w cd/casper/filesystem.manifest
chroot custom dpkg-query -W --showformat='${Package} ${Version}\n' > cd/casper/filesystem.manifest
cp cd/casper/filesystem.manifest cd/casper/filesystem.manifest-desktop 



echo "Squashfs recreation"
rm -rf cd/casper/filesystem.squashfs
mksquashfs custom cd/casper/filesystem.squashfs

echo "Create manifest"
rm -f cd/md5sum.txt
bash -c "(cd cd && find . -type f -print0 | xargs -0 md5sum > md5sum.txt)"


echo "Create iso $FILE"
dir=`pwd`
cd cd
mkisofs -r -V "Ubuntu-Live-Turtlebot" -b isolinux/isolinux.bin -c isolinux/boot.cat -cache-inodes -J -l -no-emul-boot -boot-load-size 4 -boot-info-table -o $FILE . 
cd $dir
