from shutil import copy2,copytree,rmtree
from os import scandir,remove,path
from time import time as currenttime

start_time = currenttime()
current = path.dirname(path.abspath(__file__))

def Purple(skk): return "\033[95m{}\033[00m".format(skk)
def Green(skk): return "\033[92m{}\033[00m".format(skk)
def Red(skk): return "\033[91m{}\033[00m".format(skk)
def Cyan(skk): return "\033[96m{}\033[00m".format(skk)
def Yellow(skk): return "\033[93m{}\033[00m".format(skk)

def filtercopy(old=True):
    #filter old file.
    def filter_(src, dst):
        if old == False or path.exists(dst) == False or path.getmtime(src) > path.getmtime(dst): 
            try: 
                copy2(src, dst)
            except FileNotFoundError as e: 
                print(Red(f"Updata failed: {dst} \nBecause: \"{path.dirname(dst)}\" does not exist"))
            except Exception as e: 
                print(Red(f"Updata failed: {dst} \nBecause: {e}"))
            else: 
                print(Green(f"Updata: {dst}"))
    return filter_

def ignorepath(ignore_paths,src,dst,purge=False):
    def ignore_(path_src,names):
        if purge:
            path_dst = path_src.replace(src,dst)
            if path.exists(path_dst):
                for d in list(scandir(path_dst)):
                    if d.name not in names and (d.name in ignore_paths or path.join(path_src,d.name) in ignore_paths) == False:
                        try:
                            if path.isdir(d.path): 
                                rmtree(d.path)
                            else: 
                                remove(d.path)
                        except Exception as e: 
                            print(Red(f"Delete failed: {d.path} \nBecause: {e}"))
                        else: 
                            print(Purple(f"Delete: {d.path}"))

        ignore_list = [x for x in names if x in ignore_paths or path.join(path_src,x) in ignore_paths]
        for ign in ignore_list:
            print(Cyan(f"Skip: {path.join(path_src,ign)}"))
        return ignore_list   
    return ignore_

def updata(pre_ver,ver):
    src = current + "\\battlecats" + pre_ver
    dst = current + "\\battlecats" + ver 
    #Get paths of files that are reivsed.
    Revise_path = current + "\\battlecats\\vers\\" + ver[1:]
    try:
        Revise_pathlist = []
        with open(Revise_path + "\\Revise.txt","r") as r:
            Revise_pathlist = [src + i.replace("\n","") for i in r.readlines()]
    except FileNotFoundError as e: 
        print(Yellow(f"Warning : \"Revise.txt\" in {ver[1:]} does not exist"))
    except Exception as e:
        print(Red(f"Error: {e}"))
    
    #Get paths of files that are ignored.
    try:
        ignore_pathlist = []
        with open(Revise_path + "\\ignore.txt","r") as r:
            for i in r.readlines():
                if '*' not in i:
                    ignore_pathlist.append(src + i.replace("\n",""))
                else:
                    ignore_pathlist.append(i.replace('*','').replace("\n",""))
    except FileNotFoundError as e: 
        print(Yellow(f"Warning : \"ignore.txt\" in {ver[1:]} does not exist"))
    except Exception as e:
        print(Red(f"Error: {e}"))
    
    #Copy files that not in ignore list and revise list.
    copytree(src+"\\assets", dst+"\\assets", dirs_exist_ok=True, ignore=ignorepath(Revise_pathlist+ignore_pathlist,src,dst,purge=True), copy_function=filtercopy(old=True))
    
    #Reivse files.
    for R in Revise_pathlist:
        s = path.join(Revise_path, path.basename(R))
        if path.exists(s) == False: 
            print(Red(f"{R} is not exist."))
            continue
        d = R.replace("battlecats"+pre_ver,"battlecats"+ver)
        if path.isdir(s):
            if path.exists(path.dirname(d)): 
                copytree(s,d,dirs_exist_ok=True,ignore=ignorepath(ignore_pathlist,s,d,purge=False),copy_function=filtercopy(old=True))
            else: 
                print(Red(f"Updata failed: {d} \nBecause: \"{path.dirname(d)}\" does not exist"))
        elif path.isfile(s): 
            filtercopy(old=True)(s,d)
        else: 
            continue  

vers = ["","_1.17.1","_1.18.2","_1.19.2","_1.19.3","_1.19.4","_1.20.1","_1.20.2","_1.20.4","_1.20.5"]
#rescorce_ver = {"1.17.1":7,"1.18.2":8,"1.19.2":9,"1.19.3":12,"1.19.4":13,"1.20.1":15,"1.20.2":18,"1.20.4":22,"1.20.5":32}

try:
    for i in range(1,len(vers),1): 
        print('-'*25 + vers[i].replace('_','') + '-'*25)
        updata(vers[i-1],vers[i])
except Exception as e:
    print(Red(f"Error: {e}"))

print("Finish.")
print("runtime: %s seconds" % (currenttime() - start_time))
input("Press Enter to continue...")