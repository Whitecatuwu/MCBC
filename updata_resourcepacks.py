from shutil import copy2,copytree,rmtree
from os import scandir,remove,path,rename
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
def Orange(skk): return "\033[38;5;214m{}\033[00m".format(skk) #rename


def is_valid_pathname(path) -> bool:
    from re import match
    pattern = r'^[a-zA-Z]:\\(?:[a-zA-Z0-9-_ ]+\\)*[a-zA-Z0-9-_ ]+\.\w+$'
    return match(pattern, path) is not None

def filtercopy(ignore_old=True) -> callable:
    #Ignore older files when old == True.
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

def copydata(src:str, dst:str, ignorelists:dict[str,list]=None, namespace_src:str=None, namespace_dst:str=None, purge:bool=False, ignore_old=True) -> None:
    if not path.exists(path.dirname(dst)):
        print(Red(f"Updata failed: {dst} \nBecause: \"{path.dirname(dst)}\" is not a valid path."))
        return
    
    if not path.exists(path.exists(src)):
        print(Red(f"Updata failed: {dst} \nBecause: \"{src}\" is not a valid path."))
        return
    
    if path.isdir(src):
        namespace_src = src if namespace_src == None else namespace_src
        namespace_dst = dst if namespace_dst == None else namespace_dst
        copytree(src,dst,dirs_exist_ok=True,ignore=ignorepath(ignorelists,namespace_src, namespace_dst, purge=purge),copy_function=filtercopy(ignore_old=ignore_old))
    elif path.isfile(src):
        filtercopy(ignore_old=ignore_old)(src,dst)
    else: 
        print(Red(f"Updata failed: {dst} \nBecause: \"{src}\" does not exist.")) 


def ignorepath(pathlists:dict[str, list], namespace_src:str, namespace_dst:str, purge:bool = False) -> callable:
    def _ignore(current_dirname:str, src_filenames:list) -> set:
        delete_set:set[str] = set()
        modify_set:set[str] = set()
        add_set:set[str] = set()
        rename_set:set[tuple] = set()

        ignore_set:set[str] = set()
        keep_set:set[str] = set()

        if pathlists == {} or pathlists is None:
            pass
        else:
            from fnmatch import filter as fn_filter
            #fn_filter(names, pattern)
            
            for path_D in pathlists["D"]:
                dirname,filename = path.split(*path_D)
                if current_dirname == namespace_src + dirname or dirname == "":
                    delete_set.update(set(fn_filter(src_filenames, filename)))

            for path_M in pathlists["M"]:
                dirname,filename = path.split(*path_M)
                if current_dirname == namespace_src + dirname or dirname == "":
                    modify_set.update(set(fn_filter(src_filenames, filename)))
                    add_set.add(filename) if filename not in src_filenames else None
            
            for path_R in pathlists["R"]:
                rename_src:str = path_R[0]
                rename_dst:str = path_R[1]
                rename_src_path = namespace_src + rename_src
                rename_dst_path = namespace_dst + rename_dst
                if current_dirname == path.dirname(rename_src_path):
                    copydata(rename_src_path, rename_dst_path, purge=True)
                    rename_set.add((rename_src_path, rename_dst_path))
                    ignore_set.add(path.basename(rename_src))
                elif current_dirname == path.dirname(namespace_src + rename_dst):
                    keep_set.add(path.basename(rename_dst))
            
            ignore_set = ignore_set | delete_set | modify_set

        if (purge == True) and path.exists(path_dst := current_dirname.replace(namespace_src,namespace_dst)):
            keep_set = keep_set | set(src_filenames) | modify_set | add_set
            for d in list(scandir(path_dst)):
                can_delete:bool = (d.name in delete_set) or (d.name not in keep_set)
                delete(d.path) if can_delete else None
        
        for dele in delete_set:
            print(Grey(f"Ignore src: {path.join(current_dirname,dele)}"))
        for mod in modify_set:
            print(Cyan(f"Skip src: {path.join(current_dirname,mod)}"))
        for add in add_set:
            print(Blue(f"Keep: {path.join(path_dst,add)}"))
        for ren in rename_set:
            print(Orange("Renamed: {} to {}".format(*ren)))

        return ignore_set
    return _ignore

def update(pre_ver:str,ver:str) -> None:
    src:str = current + "\\battlecats" + pre_ver
    dst:str = current + "\\battlecats" + ver 
    
    modify_path:str = current + "\\battlecats\\vers\\" + ver[1:]
    pathlists:dict[str, list] = {'R':[],'M':[],'D':[]}
    #R:rename, #M:modify, D:delete

    #Obtaining the paths of files will be modified.
    if path.exists(Modify_txt_path := modify_path + "\\Modify.txt"):
        with open(Modify_txt_path,"r") as r:
            for i in r.readlines():
                if i.startswith('#'): continue
                i = i.strip().split(':')
                pathlists[i[0]].append(tuple(i[1].split(',')))
    else:
        print(Yellow(f"Warning : \"Modify.txt\" in {ver[1:]} does not exist"))
    
    #Copy files that not in ignore list and not in modify list.
    copydata(src+"\\assets", dst+"\\assets", ignorelists=pathlists, namespace_src=src, namespace_dst=dst, purge=True)
    
    #Copy files from the path "battlecats/vers/{ver}".
    for M in pathlists["M"]:
        s:str = path.join(modify_path, path.basename(M[0]))
        d:str = dst + M[0]
        copydata(s,d,purge=True)

vers = ["", "_1.17.1", "_1.18.2", "_1.19.2", "_1.19.3", "_1.19.4", "_1.20.1", "_1.20.2", "_1.20.4", "_1.20.6"]
#resource_ver = {"1.17.1":7, "1.18.2":8, "1.19.2":9, "1.19.3":12, "1.19.4":13, "1.20.1":15, "1.20.2":18, "1.20.4":22, "1.20.6":32}

try:
    #for i in range(1,2,1): 
    for i in range(1,len(vers),1): 
        print('-'*25 + vers[i].replace('_','') + '-'*25)
        update(vers[i-1],vers[i])
except Exception as e:
    print(Red(f"Error: {e}"))

print("\nFinish.")
print("runtime: %s seconds" % (currenttime() - start_time))
#input("Press Enter to continue...")