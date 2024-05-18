from shutil import copy2,copytree,rmtree
from os import scandir,remove,path
from time import time as currenttime

start_time = currenttime()
current = path.dirname(path.abspath(__file__))

def Grey(skk): return "\033[90m{}\033[00m".format(skk) #ignore
def Red(skk): return "\033[91m{}\033[00m".format(skk) #error
def Green(skk): return "\033[92m{}\033[00m".format(skk) #update
def Yellow(skk): return "\033[93m{}\033[00m".format(skk) #warning
def Blue(skk): return "\033[94m{}\033[00m".format(skk) #keep
def Purple(skk): return "\033[95m{}\033[00m".format(skk) #delete
def Cyan(skk): return "\033[96m{}\033[00m".format(skk) #skip
def White(skk): return "\033[97m{}\033[00m".format(skk) 


def is_valid_pathname(path) -> bool:
    from re import match
    pattern = r'^[a-zA-Z]:\\(?:[a-zA-Z0-9-_ ]+\\)*[a-zA-Z0-9-_ ]+\.\w+$'
    return match(pattern, path) is not None

def filtercopy(ignore_old=True) -> callable:
    #ignore old file when old == True.
    def _filter(src, dst) -> None:
        dst_is_older:bool = (path.exists(dst) == False) or (path.getmtime(src) > path.getmtime(dst))
        if (not ignore_old) or dst_is_older: 
            try: 
                copy2(src, dst)
            except FileNotFoundError as e: 
                print(Red(f"Update failed: {dst} \nBecause: \"{path.dirname(dst)}\" does not exist"))
            except Exception as e: 
                print(Red(f"Update failed: {dst} \nBecause: {e}"))
            else: 
                print(Green(f"Update: {dst}"))
    return _filter

def delete(pathname:str) -> None:
    try:
        rmtree(pathname) if path.isdir(pathname) else remove(pathname)
    except Exception as e: 
        print(Red(f"Delete failed: {pathname} \nBecause: {e}"))
    else: 
        print(Purple(f"Delete: {pathname}"))

def ignorepath(pathlists:dict, namespace_src:str, namespace_dst:str, purge:bool = False) -> callable:
    def _ignore(path_src:str, names:list) -> set:
        delete_set:set = set()
        modify_set:set = set()
        add_set:set = set()
        ignore_set:set = set()

        if pathlists == {} or pathlists is None:
            pass
        else:
            from fnmatch import filter as fn_filter
            #fn_filter(names, pattern)
            
            for path_D in pathlists["D"]:
                dirname,filename = path.split(path_D)
                if path_src == namespace_src + dirname or dirname == "":
                    delete_set.update(set(fn_filter(names, filename)))

            for path_M in pathlists["M"]:
                dirname,filename = path.split(path_M)
                if path_src == namespace_src + dirname or dirname == "":
                    modify_set.update(set(fn_filter(names, filename)))
                    add_set.add(filename) if filename not in names else None        

            ignore_set = delete_set.union(modify_set)
    
        if (purge == True) and path.exists(path_dst := path_src.replace(namespace_src,namespace_dst)):
            for d in list(scandir(path_dst)):
                can_delete:bool = (d.name in delete_set) or (d.name not in (set(names) | modify_set | add_set) )
                delete(d.path) if can_delete else None

        for dele in delete_set:
            print(Grey(f"Ignore src: {path.join(path_src,dele)}"))
        for mod in modify_set:
            print(Cyan(f"Skip src: {path.join(path_src,mod)}"))
        for add in add_set:
            print(Blue(f"Keep: {path.join(path_dst,add)}"))

        return ignore_set
    return _ignore

def updata(pre_ver:str,ver:str) -> None:
    src:str = current + "\\battlecats" + pre_ver
    dst:str = current + "\\battlecats" + ver 
    #Get paths of files that are revised.
    modify_path:str = current + "\\battlecats\\vers\\" + ver[1:]
    pathlists:dict = {'R':[],'M':[],'D':[]}
    #R:rename, #M:modify, D:delete
    try:
        with open(modify_path + "\\Modify.txt","r") as r:
            pathlists["M"] = [i.strip() for i in r.readlines()]
    except FileNotFoundError as e: 
        print(Yellow(f"Warning : \"Modify.txt\" in {ver[1:]} does not exist"))
    except Exception as e:
        print(Red(f"Error: {e}"))
    
    #Get paths of files that are ignored.
    try:
        with open(modify_path + "\\ignore.txt","r") as r:
            pathlists["D"] = [i.strip() for i in r.readlines()]
    except FileNotFoundError as e: 
        print(Yellow(f"Warning : \"ignore.txt\" in {ver[1:]} does not exist"))
    except Exception as e:
        print(Red(f"Error: {e}"))
    
    #Copy files that not in ignore list and not in modify list.
    copytree(src+"\\assets", dst+"\\assets", dirs_exist_ok=True, ignore=ignorepath(pathlists,src,dst,purge=True), copy_function=filtercopy(ignore_old=True))
    
    #Copy files from path "battlecats/vers/{ver}".
    for R in pathlists["M"]:
        s:str = path.join(modify_path, path.basename(R))
        if path.exists(s) == False: 
            #print(Red(f"{src + R} does not exist."))
            print(Red(f"{s} does not exist."))
            continue
        d:str = dst + R

        if not path.exists(path.dirname(d)):
            print(Red(f"Updata failed: {d} \nBecause: \"{path.dirname(d)}\" does not exist"))
        else: 
            if path.isdir(s):
                copytree(s,d,dirs_exist_ok=True,ignore=ignorepath(None,s,d,purge=True),copy_function=filtercopy(ignore_old=True))
            elif path.isfile(s): 
                filtercopy(ignore_old=True)(s,d)
            else: 
                print(Red(f"Updata failed: {d} \nBecause: \"{s}\" is not a valid path.")) 

vers = ["", "_1.17.1", "_1.18.2", "_1.19.2", "_1.19.3", "_1.19.4", "_1.20.1", "_1.20.2", "_1.20.4", "_1.20.6"]
#resource_ver = {"1.17.1":7, "1.18.2":8, "1.19.2":9, "1.19.3":12, "1.19.4":13, "1.20.1":15, "1.20.2":18, "1.20.4":22, "1.20.6":32}

try:
    #for i in range(1,2,1): 
    for i in range(1,len(vers),1): 
        print('-'*25 + vers[i].replace('_','') + '-'*25)
        updata(vers[i-1],vers[i])
except Exception as e:
    print(Red(f"Error: {e}"))

print("\nFinish.")
print("runtime: %s seconds" % (currenttime() - start_time))
#input("Press Enter to continue...")