#!/usr/bin/ksh
tmpdir=`dirname $0`
curdir=`pwd`
verfileall=$curdir/version.ini
verfiletmp=$curdir/version.ini.$$
verfiletmpbak=$curdir/version.ini.$$.bak
verfilelist=$tmpdir/vername

#检查新增的version.ini
cd $tmpdir
ls version.ini > $verfilelist
if [ ! -s $verfilelist ]; then
    cd ..
    rm -rf $tmpdir
    exit 0
fi

verfilenew=`cat $verfilelist`
verfilenew=$tmpdir/$verfilenew

#如果不需要合并，则将.BIN中tar开的内容拷过来
if [ ! -s $verfileall ]; then
     #E8742 guojian 2002-08-17 below
     #cp $tmpdir/* .
     cp $tmpdir/* $curdir
     #E8742 guojian 2002-08-17 above
     cd /tmp
     rm -rf $tmpdir
     exit 0
fi

#合并配置文件，如有相同行取版本新的
cp $verfileall $verfiletmp
rm -rf $verfileall
sed -e "s/	/ /g" $verfilenew > $verfileall
cp $verfileall $verfilenew
sed -e "s/	/ /g" $verfiletmp > $verfileall
cp $verfileall $verfiletmp
rm -rf $verfileall
touch $verfileall
OLD_IFS=$IFS
IFS=' '
OS=`uname`
while read field1 field2 field3 field4 field5 field6
do
    if [ "-$field1" = "-" ]; then
        continue
    fi
    if [ "-$OS" = "-SunOS" ]; then
        result=`cat $verfiletmp | grep -w $field1`
    else    
        result=`awk -v field_var=$field1 '{if($1 == field_var) print $0}' $verfiletmp`
    fi
    if [ "-$result" = "-" ]; then
        echo $field1" "$field2" "$field3" "$field4" "$field5" "$field6 >> $verfileall
        cp $tmpdir/$field1 $curdir
    else
    	newfield1=`echo $result | awk '{print $1}'`
        newpartfield3=`echo $result | awk '{print $3}'| cut -c5-12`
        partfield3=`echo $field3 | cut -c5-12`
        if [ $partfield3 -gt $newpartfield3 ]; then
            echo $field1" "$field2" "$field3" "$field4" "$field5" "$field6 >> $verfileall
            cp $verfiletmp $verfiletmpbak
            if [ "-$OS" = "-SunOS" ]; then
                cat $verfiletmpbak | grep -vw $newfield1 > $verfiletmp
            else    
                awk -v field_var=$newfield1 '{if ($1 != field_var) print $0}' $verfiletmpbak > $verfiletmp
            fi
            cp $tmpdir/$field1 $curdir
        fi
    fi
done < $verfilenew
IFS=$OLD_IFS
cat $verfiletmp >> $verfileall
rm -rf $verfiletmp
rm -rf $verfiletmpbak
cd $tmpdir
cd ..
rm -rf $tmpdir
echo "update packet install OK!"
exit 0