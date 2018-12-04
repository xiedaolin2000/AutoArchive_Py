#!/bin/sh
#################################################################
#     Install Everywhere V1.0                                   #
#     Author: David Lee                                         #
#     Date 2001-07-04                                           #
#################################################################
# Filename of self extractor to generate.
if [ $# -ne 3 ]; then
  echo $#
  echo "Usage: Copy all files to install into a path, then run:"
  echo "       makeinstall.sh <dataPath> <invokeProgram> <targetFilename>"
  echo "       This shell will create a single self extractor which name is"
  echo "       <targetFilename> and contains all file in <dataPath>,"
  echo "       and when run <targetFilename>, after extract all data file,"
  echo "       it will call <invokeProgram> echo automatically. "
  echo "       and <invokeProgram> will finished the rest install work."
fi
PWD=`pwd`
TARGET=$3
if [ -f "$TARGET" ]; then
  echo "Warning: $TARGET already exist on current path, overlay it? (Y/N):[N]\c"
  read IN
  if [ "x$IN" != "xY" -a "x$IN" != "xy" ]; then
    exit 0
  fi  
fi
cd $1
if [ $? -ne 0 ]; then
  echo "Can not enter into path $1"
  exit 1
fi
CONTENT=`pwd`

# Check whether autorun file exist
if [ ! -r "$2" ]; then
  echo "Can't read autorun file $2"
  exit 2
fi
RUN=$2

# Total extract shell file length
LEN="@@@"
chmod a+x $RUN

# Generate Self extract shell
echo '#!/bin/sh
INSTALL_PROGRAM_NAME=`basename $0` ; export INSTALL_PROGRAM_NAME
INSTALL_PROGRAM_ARGS="$*" ; export INSTALL_PROGRAM_ARGS
INSTALL_PROGRAM_COMMAND_LINE="$0 $*" ; export INSTALL_PROGRAM_COMMAND_LINE
CURRENT_PATH=`pwd`
cd `dirname $0`
INST=`pwd`/`basename $0`
cd /tmp
TMPDIR=/tmp/installeverywhere.$$

# Trap ctrl-C
trap "rm -rf $TMPDIR ; exit 999" 2
mkdir $TMPDIR
cd $TMPDIR' >../$TARGET.tmp.$$
echo "cat \$INST |tail +${LEN}c|tar xf -" >>../$TARGET.tmp.$$
echo 'cd $CURRENT_PATH'>>../$TARGET.tmp.$$
echo "/tmp/installeverywhere.\$\$/$RUN \$*" >>../$TARGET.tmp.$$
echo 'cd ..
rm -rf installeverywhere.$$
exit 0' >>../$TARGET.tmp.$$

LEN=`ls -l ../$TARGET.tmp.$$ |awk '{ print $5}'`
LEN=`expr $LEN + 1`
sed -e "s/@@@/$LEN/g" ../$TARGET.tmp.$$ >../$TARGET
rm ../$TARGET.tmp.$$

# Add install data
tar cf - * >>../$TARGET
chmod a+x ../$TARGET
echo "Install file $TARGET generate successfully."