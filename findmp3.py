#!/usr/bin/python
# −*− coding: UTF−8 −*−

import sys
import re
from hashlib import md5
from hsaudiotag import id3v2,id3v1
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
    collision=defaultdict(set)
    to_move=defaultdict(set)
    def __init__(self,**args):
        for k,v in args.items():
            setattr(self,k,v)
    
    def show_collision(self):
        msg=u""
        for md5, fn_list in self.collision.items():
            msg+= "%s <=> %s collides with %s \n" % (
            md5 , self.mp3list[md5]["dst"] , "\n\t".join(fn_list) 
        )
        return msg
        
    def explore(self):
        print "src=%s\ndst=%s" % (self.src_dir, self.dst_dir)
        def mp3_res(fullname):
            res=dict()
            v2=id3v2.Id3v2(fullname)
            v1=id3v1.Id3v1(fullname)
            for to_get in ["album", "artist", "title" ]:
                v1_val = v1.exists and getattr(v1,to_get) or u""
                v2_val = v2.exists and getattr(v2,to_get) or u""
                res[to_get] = len(v1_val) > len(v2_val) and unicode(v1_val) or unicode(v2_val)
                if 0 == len(res[to_get]):
                    res[to_get]=u"unknown"
            return res

                    
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
                                    
                    collision=False
                    well_placed=False
                    already_exists=False
                    print fullname
                    mp3info=mp3_res(fullname)
                        
                    print mp3info["album"]
                    print mp3info["artist"]
                    with open(fullname, "r") as g:
                        md5s=md5(g.read()).hexdigest()
                    dst=""
                    try:
                        dst=unicode(path.normcase(
                                path.join(
                                    self.dst_dir,
                                    re.sub('/\'','',mp3info["artist"]), 
                                    re.sub('\/','',mp3info["album"]), 
                                    mp3 )
                                )
                            )
                    except: 
                        print mp3.__repr__()
                        mp3=mp3.decode("utf8")
                        dst=path.normcase(path.join(self.dst_dir,re.sub('/\'','',mp3info["artist"]), re.sub('\/','',mp3info["album"]),  mp3 ))
                        raise Exception("Encode de l'utfU?????")

                    if  path.isfile(dst):
                        already_exists = True
                        with open(dst, "r") as f:
                            md5d=md5(f.read()).hexdigest()
                        if md5d != md5s:
                            collision = True
                            raise Exception("*%s*!=*%s* exists with different md5 :%s!=%s" % ( fullname , dst, md5s,md5d ))
                        else:
                            well_placed = fullname == dst

                    if collision:
                        self.collision[md5s].add( fullname )
                    else:
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
                            dst=dst,
                            well_placed = well_placed,
                            **mp3info

                            )
                    print """
                    
                    %s => 
                        dst     = %s 
                        artist  = %s
                        album   = %s""" % ( md5s,dst, mp3info["artist"],mp3info["album"]) 
            
        for ldir in self.src_dir:
            print ldir
            path.walk(ldir, show, ".*\.(mp3|MP3)$")

        
    def apply_strategy(self, **strategy):
        if len(self.collision.keys()):
            raise Exception(self.show_collision() )
        for target,strategy in strategy.items():
            real_target=getattr(self, target)

            for index,item in enumerate(real_target.items()):
                    strategy(self,index, *item)


cleaner=Mp3Cleaner(dst_dir = sys.argv[2], src_dir= [ sys.argv[1] ])
cleaner.explore()
 
print "*" * 75
print "to remove = %s" % "\n".join( "\nand\t".join(v) for v in cleaner.to_remove.values() ) 
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
            raise Exception("Same file %s") % to_copy
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

cleaner.apply_strategy(to_move= move_mp3, to_remove = remove_mp3)


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
