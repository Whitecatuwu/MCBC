from shutil import copy2,copytree,rmtree
from os import chdir,scandir,remove,path,makedirs
from time import time as currenttime

current = path.dirname(path.abspath(__file__))
chdir(current)

def Grey(skk): return "\033[90m{}\033[00m".format(skk) #ignore
def Red(skk): return "\033[91m{}\033[00m".format(skk) #error
def Green(skk): return "\033[92m{}\033[00m".format(skk) #update
def Yellow(skk): return "\033[93m{}\033[00m".format(skk) #warning
def Blue(skk): return "\033[94m{}\033[00m".format(skk) #keep
def Purple(skk): return "\033[95m{}\033[00m".format(skk) #delete
def Cyan(skk): return "\033[96m{}\033[00m".format(skk) #skip
def White(skk): return "\033[97m{}\033[00m".format(skk)
def Orange(skk): return "\033[38;5;214m{}\033[00m".format(skk) #rename
def Strong(skk): return "\033[1m{}\033[0m".format(skk)

def is_valid_pathname(path) -> bool:
    from re import match
    pattern = r'^[a-zA-Z]:\\(?:[a-zA-Z0-9-_ ]+\\)*[a-zA-Z0-9-_ ]+\.\w+$'
    return match(pattern, path) is not None

def isparent_dir(path_parent:str, path_child:str) -> bool:
    commonpath = path.commonpath((path_parent,path_child))
    return (commonpath == path_parent) 

def get_top_dirname(thepath:str) -> bool:
    while True:
        thepath, tail = path.split(thepath)
        if thepath == '\\' or thepath == '/':
            return tail
        
def issamepath(path_a:str, path_b:str) -> bool:
    return path_a.lower() == path_b.lower()

def filtercopy(ignore_old=True) -> callable:
    #Ignore older files when ignore_old is True.
    def _filter(src, dst) -> None:
        dst_is_older:bool = (not path.exists(dst)) or (path.getmtime(src) > path.getmtime(dst))
        if (not ignore_old) or dst_is_older: 
            try: 
                copy2(src, dst)
            except Exception as e: 
                print(Red(f"Update failed: {dst} \nBecause: {e}\n"))
            else: 
                print(Green(f"Update: {dst}"))
    return _filter

def delete(pathname:str) -> None:
    try:
        rmtree(pathname) if path.isdir(pathname) else remove(pathname)
    except Exception as e: 
        print(Red(f"Delete failed: {pathname} \nBecause: {e}\n"))
    else: 
        print(Purple(f"Delete: {pathname}"))

def copydata(src:str, dst:str, ignorelists:dict[str,list]=None, namespace_src:str=None, namespace_dst:str=None, purge:bool=False, ignore_old=True) -> bool:
    if not path.exists(src):
        print(Red(f"Updata failed: {dst} \nBecause: \"{src}\" does not exist.\n"))
        return False
    
    if path.isdir(src):
        namespace_src = src if namespace_src == None else namespace_src
        namespace_dst = dst if namespace_dst == None else namespace_dst
        copytree(src,dst,dirs_exist_ok=True,ignore=ignorepath(ignorelists,namespace_src, namespace_dst, purge=purge),copy_function=filtercopy(ignore_old=ignore_old))
        return True
    elif path.isfile(src):
        filtercopy(ignore_old=ignore_old)(src,dst)
        return True
    else: 
        print(Red(f"Updata failed: {dst} \nBecause: \"{src}\" is not a directory or a file.\n"))
        return False

def ignorepath(pathlists:dict[str, list], namespace_src:str, namespace_dst:str, purge:bool = False) -> callable:
    def _ignore(current_dirname:str, src_filenames:list) -> set:
        delete_set:set[str] = set()
        modify_set:set[str] = set()
        add_set:set[str] = set()

        ignore_set:set[str] = set()
        keep_set:set[str] = set(src_filenames)

        if pathlists == {} or pathlists is None:
            pass
        else:
            from fnmatch import filter as fn_filter
            #fn_filter(names, pattern)
            dirname:str
            filename:str
            
            for path_D in pathlists["D"]:
                path_D = path_D[0]
                dirname, filename = path.split(path_D)
                dirname = namespace_src + dirname
                if issamepath(current_dirname, dirname) or dirname == namespace_src:
                    names_set:set = set(fn_filter(src_filenames, filename))
                    delete_set.update(names_set)
                    if not names_set and (not dirname == namespace_src): print(Yellow(f"Warning : There were no results found for {filename} in \"{dirname}\"."))

            for path_M in pathlists["M"]:
                path_M = path_M[0]
                dirname, filename = path.split(path_M)
                dirname = namespace_src + dirname
                if issamepath(current_dirname, dirname) or dirname == namespace_src:
                    names_set:set = set(fn_filter(src_filenames, filename))
                    modify_set.update(names_set)
                    if not names_set and (not dirname == namespace_src): print(Yellow(f"Warning : There were no results found for {filename} in \"{dirname}\"."))

            for path_A in pathlists["A"]:
                path_A = path_A[0]
                add_path:str = namespace_src + path_A
                if isparent_dir(current_dirname, add_path):
                    filename = get_top_dirname(add_path.replace(current_dirname,""))
                    if filename not in src_filenames : add_set.add(filename)
            
            for path_R in pathlists["R"]:
                rename_src_dir, rename_src_file = path.split(path_R[0])
                rename_dst_dir, rename_dst_file = path.split(path_R[1])
                rename_src_path = namespace_src + path_R[0]
                rename_dst_path = namespace_dst + path_R[1]
                  
                if issamepath(current_dirname, namespace_src + rename_src_dir):
                    ignore_set.add(rename_src_file)
                    keep_set.discard(rename_src_file)
                    #if path.exists():
                        #delete()
                    if copydata(rename_src_path, rename_dst_path,ignorelists=pathlists, purge=True,namespace_src=namespace_src,namespace_dst=namespace_dst): 
                        print(Orange("Rename: \"{}\" to\n \"{}\"\n".format(rename_src_path,rename_dst_path)))

                keep_renamed_path:str = namespace_src + rename_dst_dir
                if issamepath(current_dirname, keep_renamed_path):
                    keep_set.add(rename_dst_file)
                elif isparent_dir(current_dirname, keep_renamed_path):
                    filename = get_top_dirname(keep_renamed_path.replace(current_dirname,""))
                    keep_set.add(filename)
            
        ignore_set = ignore_set | delete_set | modify_set
        keep_set = keep_set | modify_set | add_set
        keep_set.difference_update(delete_set)

        if (purge == True) and path.exists(path_dst := current_dirname.replace(namespace_src,namespace_dst)):
            for d in scandir(path_dst):
                if d.name not in keep_set : delete(d.path)
        
        for dele in delete_set:
            print(Grey(f"Ignore src: {path.join(current_dirname,dele)}"))
        for mod in modify_set:
            print(Cyan(f"Skip src: {path.join(current_dirname,mod)}"))
        for add in add_set:
            print(Blue(f"Keep: {path.join(path_dst,add)}"))

        return ignore_set
    return _ignore

def update(pre_ver:str,ver:str) -> None:
    src:str = current + "\\battlecats" + pre_ver
    dst:str = current + "\\battlecats" + ver 
    
    modify_path:str = current + "\\battlecats\\vers\\" + ver[1:]
    #R:rename, #M:modify, D:delete, A:add
    pathlists:dict[str, list] = {'R':[],'M':[],'D':[],'A':[]}

    #Obtaining the paths of files will be modified.
    if path.exists(Modify_txt_path := modify_path + "\\Modify.txt"):
        with open(Modify_txt_path,"r") as r:
            for i in r.readlines():
                if i.startswith('#'): continue
                i = i.strip().split(':')
                if i[0] in pathlists.keys(): pathlists[i[0]].append(tuple(i[1].split(',')))
    else:
        print(Yellow(f"Warning: \"Modify.txt\" in {ver[1:]} does not exist, it will be added."))
        if not path.exists(path.dirname(Modify_txt_path)): makedirs(path.dirname(Modify_txt_path))
        with open(Modify_txt_path,"w"): pass

    #Copy files that not in ignore list and not in modify list.
    copydata(src+"\\assets", dst+"\\assets", ignorelists=pathlists, namespace_src=src, namespace_dst=dst, purge=True)
    
    #Copy files from the path "battlecats/vers/{ver}".
    for MA in pathlists["M"] + pathlists["A"]:
        s:str = path.join(modify_path, path.basename(MA[0]))
        d:str = dst + MA[0]
        copydata(s,d,ignorelists=pathlists, purge=True,namespace_src=src,namespace_dst=dst)

def main():
    vers = ["", "_1.17.1", "_1.18.2", "_1.19.2", "_1.19.3", "_1.19.4", "_1.20.1", "_1.20.2", "_1.20.4", "_1.20.6"]
    older_vers = ["", "_1.16.5", "_1.16.1", "_1.14.4", "_1.12.2", "_1.10.2", "_1.8.9"]
    #resource_ver = {"1.8.9":1, "1.10.2":2, "1.12.2":3, "1.14.4":4, "1.16.1":5, "1.16.5":6, "1.17.1":7, "1.18.2":8, "1.19.2":9, "1.19.3":12, "1.19.4":13, "1.20.1":15, "1.20.2":18, "1.20.4":22, "1.20.6":32}
    
    #for i in range(1,2,1): 
    for i in range(1,len(older_vers),1):
        print(Strong('-'*25 + older_vers[i].replace('_','') + '-'*25))
        update(older_vers[i-1],older_vers[i])

    #for i in range(1,2,1): 
    for i in range(1,len(vers),1): 
        print(Strong('-'*25 + vers[i].replace('_','') + '-'*25))
        update(vers[i-1],vers[i])

if __name__ == '__main__':
    start_time = currenttime()
    main()
    print("\nFinish.")
    print("runtime: %s seconds" % (currenttime() - start_time))
    #input("Press Enter to continue...")