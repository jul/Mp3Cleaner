#!/usr/bin/python
# −*− coding: UTF−8 −*−

import sys
import re
from hashlib import md5
from hsaudiotag import id3v2 as id3
from collections import defaultdict

from shutil import move,copy
from os import remove,path,makedirs

path.supports_unicode_filenames=True
class Mp3Cleaner:
    dst_dir=u"/fake"
    mp3list=defaultdict(dict)
    src_dir=[]
    to_remove=defaultdict(set)
    well_placed=defaultdict(set)
    to_move=defaultdict(set)
    def __init__(self,**args):
        for k,v in args.items():
            setattr(self,k,v)

    def explore(self):
        print "src=%s\ndst=%s" % (self.src_dir, self.dst_dir)
        def show(arg, dir, files):
            files= [ f for f in files if re.match(arg,f) ]
            if len(files):
                for mp3 in files:
                    if not  isinstance(mp3, unicode):
                        mp3=unicode(mp3,"utf8")
                    if not  isinstance(dir, unicode):
                        dir=unicode(dir,"utf8")
                    try:
                        #fullname = path.realname(fullname)
                        fullname=unicode(path.normcase(path.join(dir, mp3)))
                    except:
                        print mp3 + ",".join([ "**%2x,%s**" % ( ord(c),c )   for c in mp3  if ord(c) > 126 ]) 
                        mp3=mp3.decode('utf-8')

                        raise Exception("Fiuck %s" % mp3.__repr__())
                                    

                    well_placed=False
                    already_exists=False
                    mp3info=id3.Id3v2(fullname)
                    artist=mp3info.exists and mp3info.artist or u"unknown"
                    album=mp3info.exists and  mp3info.album or u"unknown"
                    songname=mp3info.exists and  unicode( mp3info.title + u".mp3") or unicode( mp3 )
                    print fullname
                    print album
                    print artist
                    with open(fullname, "r") as g:
                        md5s=md5(g.read()).hexdigest()
                    dst=""
                    #dst=path.join(dst_dir,re.sub('/','',artist), re.sub('/','',album), mp3)
                    try:
                        dst=unicode(path.normcase(path.join(self.dst_dir,re.sub('/\'','',artist), re.sub('\/','',album),  songname )))
                    except: 
                        print mp3.__repr__()
                        mp3=mp3.decode("utf8")
                        dst=path.normcase(path.join(self.dst_dir,re.sub('/\'','',artist), re.sub('\/','',album),  songname ))

                    if  path.isfile(dst):
                        already_exists = True
                        with open(dst, "r") as f:
                            md5d=md5(f.read()).hexdigest()
                        if md5d != md5s:
                            raise KeyError("*%s*!=*%s* exists with different md5 :%s!=%s" % ( fullname , dst, md5s,md5d ))
                        else:
                            well_placed = fullname == dst
                            print "%s == %s ? %s" % (fullname , dst, "True" if well_placed else "False")


                    
                    if  already_exists and not well_placed :
                        self.to_remove[md5s].add(  fullname )
                    if not already_exists and not well_placed: 
                        if self.to_move.has_key(md5s):
                            self.to_remove[md5s].add( fullname )
                        else:
                            self.to_move[md5s].add( fullname )
                    if already_exists and well_placed:
                        self.well_placed[md5s].add( fullname )
                    if not already_exists and well_placed:
                        raise Exception("OMG !!!!")


                    if not self.mp3list.has_key(md5s):
                        self.mp3list[md5s] = dict(
                            src = fullname ,
                            artist=artist,
                            album=album,
                            dst=dst,
                            well_placed = well_placed
                            )
                    print """
                    
                    %s => 
                        dst     = %s 
                        artist  = %s
                        album   = %s""" % ( md5s,dst, artist,album) 
            
        for ldir in self.src_dir:
            print ldir
            path.walk(ldir, show, ".*\.(mp3|MP3)$")

        
    def apply_strategy(self, **strategy):
        for target,strategy in strategy.items():
            real_target=getattr(self, target)

            for index,item in enumerate(real_target.items()):
                    strategy(self,index, *item)


cleaner=Mp3Cleaner(dst_dir = sys.argv[2], src_dir= [ sys.argv[1] ])
cleaner.explore()
 
print "*" * 75
print "to remove = %s" % "\n".join( cleaner.mp3list[k]["src"] for k in cleaner.to_remove ) 
print "*" * 75
def remove_mp3(cls, i , k, v):
    removed=[]
    for to_remove in v:
        remove(to_remove)
        removed += [ to_remove ]
    
    for v in removed:
        cls.to_remove[k].discard(v)

def transfer_mp3(cls, i, k,v):
    print "create dir if not exists"
    mp3=cls.mp3list[k]
    copied=set()
    dst_dir=path.dirname(mp3["dst"])
    if len(v) > 1:
        raise Exception( "len > 1 pour %s" % v)
    if not path.isdir(dst_dir):
        makedirs(dst_dir)    
    for  to_copy in v :
        print "cp **%s** => %s"  % (unicode(to_copy),unicode( mp3["dst"]))
        if mp3["well_placed"]:
            print "dont copy but move"
        else:
            
            if not path.isfile(to_copy):
                raise Exception("wtf %s" % to_move )
            copy(to_copy,mp3["dst"])
            copied.add(to_copy)

    for v in copied:
        cls.mp3list[k]["src"]=v
        cls.mp3list[k]["well_placed"]=True

def move_mp3(cls, i, k,v):
    print "create dir if not exists"
    mp3=cls.mp3list[k]
    to_remove=set()
    dst_dir=path.dirname(mp3["dst"])
    if len(v) > 1:
        raise Exception( "len > 1 pour %s" % v)
    if not path.isdir(dst_dir):
        makedirs(dst_dir)    
    for  to_move in v :
        print "mv **%s** => %s"  % (to_move, mp3["dst"])
        if not path.isfile(to_move):
            raise Exception("wtf %s" % to_move )
        move(to_move,mp3["dst"])
        to_remove.add(to_move)
    for v in to_remove: 
        cls.to_move[k].discard(v)
        cls.mp3list[k]["src"]=v
        cls.mp3list[k]["well_placed"]=True
print  "\n".join( "%16s=>%d" % (
        k , 
        sum( 
            [ len(vv) for vv in  getattr(cleaner,k).values() ] 
        ) 
    ) for k in [ 'to_move','to_remove','well_placed' ] )
cleaner.apply_strategy(to_move= transfer_mp3)


print  "\n".join( "%16s=>%d" % (
        k , 
        sum( 
            [ len(vv) for vv in  getattr(cleaner,k).values() ] 
        ) 
    ) for k in [ 'to_move','to_remove','well_placed' ] )
print "dst = %s" % cleaner.dst_dir
#for md5,file_list in doublon.items():
#    print "%s has same info as\n\t%s" % ( mp3list[md5]['file'], ",".join(file_list))

print """
RESULT
------"""
