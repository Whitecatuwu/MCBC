from shutil import copy2,copytree,rmtree
from os import scandir,remove,path
from time import time as currenttime

start_time = currenttime()
current = path.dirname(path.abspath(__file__))

def Grey(skk): return "\033[90m{}\033[00m".format(skk) #ignore
def Red(skk): return "\033[91m{}\033[00m".format(skk) #error
def Green(skk): return "\033[92m{}\033[00m".format(skk) #update
def Yellow(skk): return "\033[93m{}\033[00m".format(skk) #warning
def Blue(skk): return "\033[94m{}\033[00m".format(skk) 
def Purple(skk): return "\033[95m{}\033[00m".format(skk) #delete
def Cyan(skk): return "\033[96m{}\033[00m".format(skk) #skip
def White(skk): return "\033[97m{}\033[00m".format(skk) 


def is_valid_pathname(path):
    from re import match
    pattern = r'^[a-zA-Z]:\\(?:[a-zA-Z0-9-_ ]+\\)*[a-zA-Z0-9-_ ]+\.\w+$'
    return match(pattern, path) is not None

def filtercopy(old=True) -> callable:
    #ignore old file when old == True.
    def _filter(src, dst) -> None:
        cancopy:bool = (old == False) or (path.exists(dst) == False) or (path.getmtime(src) > path.getmtime(dst))
        if cancopy: 
            try: 
                copy2(src, dst)
            except FileNotFoundError as e: 
                print(Red(f"Update failed: {dst} \nBecause: \"{path.dirname(dst)}\" does not exist"))
            except Exception as e: 
                print(Red(f"Update failed: {dst} \nBecause: {e}"))
            else: 
                print(Green(f"Update: {dst}"))
    return _filter

def ignorepath(pathlist:dict,src,dst,purge=False) -> callable:
    def _ignore(path_src,names) -> set:
        from fnmatch import filter as fn_filter
        #fn_filter(names, pattern)
        delete_list = [x for x in names if path.join(path_src,x) in [src+p for p in pathlist["D"]]]
        for fi in filter(lambda x:not path.isabs(x),pathlist["D"]):
            delete_list.extend(fn_filter(names, fi))
        delete_list = set(delete_list)

        modify_list = [x for x in names if path.join(path_src,x) in [src+p for p in pathlist["M"]]]
        for fi in filter(lambda x:not path.isabs(x),pathlist["M"]):
            modify_list.extend(fn_filter(names, fi))
        modify_list = set(modify_list)

        ignore_list = delete_list | modify_list
    
        if purge:
            path_dst = path_src.replace(src,dst)
            if path.exists(path_dst):
                for d in list(scandir(path_dst)):
                    can_delete:bool = (d.name in delete_list) or ( (d.name not in names) and (path.join(path_dst,d.name) not in [dst+p for p in pathlist["M"]]) )
                    if  can_delete:
                        try:
                            if path.isdir(d.path): 
                                rmtree(d.path)
                            else: 
                                remove(d.path)
                        except Exception as e: 
                            print(Red(f"Delete failed: {d.path} \nBecause: {e}"))
                        else: 
                            print(Purple(f"Delete: {d.path}"))

        for ign in delete_list:
            print(Grey(f"Ignore: {path.join(path_src,ign)}"))
        for mod in modify_list:
            print(Cyan(f"Skip: {path.join(path_src,mod)}"))
        return ignore_list
    return _ignore

def updata(pre_ver:str,ver:str) -> None:
    src = current + "\\battlecats" + pre_ver
    dst = current + "\\battlecats" + ver 
    #Get paths of files that are reivsed.
    Revise_path = current + "\\battlecats\\vers\\" + ver[1:]
    pathlist = {'R':[],'M':[],'D':[]}
    #R:rename, #M:modify, D:delete
    try:
        with open(Revise_path + "\\Revise.txt","r") as r:
            pathlist["M"] = [i.strip() for i in r.readlines()]
    except FileNotFoundError as e: 
        print(Yellow(f"Warning : \"Revise.txt\" in {ver[1:]} does not exist"))
    except Exception as e:
        print(Red(f"Error: {e}"))
    
    #Get paths of files that are ignored.
    try:
        with open(Revise_path + "\\ignore.txt","r") as r:
            pathlist["D"] = [i.strip() for i in r.readlines()]
    except FileNotFoundError as e: 
        print(Yellow(f"Warning : \"ignore.txt\" in {ver[1:]} does not exist"))
    except Exception as e:
        print(Red(f"Error: {e}"))
    
    #Copy files that not in ignore list and revise list.
    copytree(src+"\\assets", dst+"\\assets", dirs_exist_ok=True, ignore=ignorepath(pathlist,src,dst,purge=True), copy_function=filtercopy(old=True))
    
    #Reivse files.
    for R in pathlist["M"]:
        s = path.join(Revise_path, path.basename(R))
        if path.exists(s) == False: 
            print(Red(f"{src + R} is not exist."))
            continue
        d = dst + R
        if path.isdir(s):
            if path.exists(path.dirname(d)): 
                copytree(s,d,dirs_exist_ok=True,copy_function=filtercopy(old=True))
            else: 
                print(Red(f"Updata failed: {d} \nBecause: \"{path.dirname(d)}\" does not exist"))
        elif path.isfile(s): 
            filtercopy(old=True)(s,d)
        else: 
            continue  

vers = ["","_1.17.1","_1.18.2","_1.19.2","_1.19.3","_1.19.4","_1.20.1","_1.20.2","_1.20.4","_1.20.6"]
#resource_ver = {"1.17.1":7,"1.18.2":8,"1.19.2":9,"1.19.3":12,"1.19.4":13,"1.20.1":15,"1.20.2":18,"1.20.4":22,"1.20.6":32}

try:
    for i in range(1,len(vers),1): 
        print('-'*25 + vers[i].replace('_','') + '-'*25)
        updata(vers[i-1],vers[i])
except Exception as e:
    print(Red(f"Error: {e}"))

print("Finish.")
print("runtime: %s seconds" % (currenttime() - start_time))
input("Press Enter to continue...")