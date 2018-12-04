#!/usr/bin/ksh
#################################################################
#     Make  BIN V1.0                                            #
#     Author: Gao xuehua                                        #
#     Date  : 2006-07-20                                        #
#################################################################

if [ $# -ne 2 ]; then
  echo "参数个数必须为2,第一个参数表示SMAP RUN包的ZIP,第二个参数表示目标BIN文件."
  exit 0
fi

targetzip=$1
targetname=$2

unzip -oa ${targetzip}
rm -rf ${targetzip}

awk '{print $1"|"$2}' version.ini > tar.tmp
while read file
do
    des=`echo $file | cut -d'|' -f1`
    source=`echo $file | awk -F'|' '{print $NF}'`
    zip  ${des} ${source}
done < tar.tmp

rm tar.tmp

mv makeinstall.sh ../

ls -l|awk '{printf "%s\n", $9}' > tar.tmp

while read file
do
	filename=`echo $file | awk '{print $1}'`
  	postfix=`echo $file | awk -F'.' '{print $NF}'`

  	if [ "-$file" != "-install_upd.sh" -a "-$file" != "-version.ini" ];then
  	    if [ "-$postfix" != "-zip" ];then
    	    rm -rf ${filename}
    	fi
  	fi

done < tar.tmp

rm tar.tmp

updir=`pwd |awk -F'/' '{print $NF}'`

cd ..
chmod +x makeinstall.sh
makeinstall.sh ${updir} install_upd.sh ${targetname}

cd ${updir}
rm *
mv ../${targetname} ${targetname}
chmod +x ${targetname}

exit 0
