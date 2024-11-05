from shutil import copy2,copytree,rmtree
from os import chdir,scandir,remove,path,makedirs
from time import time as currenttime
from re import match
from fnmatch import filter as fn_filter
#import threading

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

def is_valid_pathname(pathname:str) -> bool:
    ###"""invalid: {\, /, *, ?, :, ", <, >, |}"""
    #assert isinstance(pathname,str)
    pathname = pathname.replace('/','\\')
    pattern = r'(([a-zA-Z]:\\)|\.{0,2}\\)?([^\\/:*?"<>|]+\\)*([^\\/*?:"<>|]+(\.[^\\/*?:"<>|]+)*)$'
    #pattern = r'(([a-zA-Z]:\\)|\.{0,2}\\)?(\w+\\)*(\w+(\.\w+)*)$'
    return (match(pattern, pathname) is not None)

def isparent_dir(path_parent:str, path_child:str) -> bool:
    if len(path_child) < len(path_parent): return False

    path_parent = path_parent.replace('/','\\')
    path_child = path_child.replace('/','\\')
    spilt_parent = path_parent.split('\\')
    spilt_child = path_child.split('\\')

    for p,c in zip(spilt_parent,spilt_child):
        if not fn_filter([c],p) : return False
    return True

def get_top_dirname(thepath:str) -> str:
    assert is_valid_pathname(thepath)
    thepath = thepath.replace("/","\\").strip("\\")
    return thepath.split('\\')[0]

def filtercopy(ignore_old=True,_:list=[False]) -> callable:
    ##Ignore older files when ignore_old is True.
    def _filter(src, dst) -> None:
        dst_is_older:bool = (not path.exists(dst)) or (path.getmtime(src) > path.getmtime(dst))
        if (not ignore_old) or dst_is_older: 
            try: 
                copy2(src, dst)
            except Exception as e: 
                print(Red(f"Update failed: {dst} \nBecause: {e}\n"))
            else: 
                print(Green(f"Update: {dst}"))
                _[0] = True
    return _filter

def delete(pathname:str) -> None:
    if not path.exists(pathname):
        return
    try:
        rmtree(pathname) if path.isdir(pathname) else remove(pathname)
    except Exception as e: 
        print(Red(f"Delete failed: {pathname} \nBecause: {e}\n"))
    else: 
        print(Purple(f"Delete: {pathname}"))

def copydata(src:str, dst:str, ignorelists:dict[str,list]=None, namespace_src:str=None, namespace_dst:str=None, purge:bool=False, ignore_old=True, _:list=[False]) -> bool:
    if not path.exists(src):
        print(Red(f"Updata failed: {dst} \nBecause: \"{src}\" does not exist.\n"))
        return False
    if path.isdir(src):
        namespace_src = src if namespace_src == None else namespace_src
        namespace_dst = dst if namespace_dst == None else namespace_dst
        copytree(src,dst,dirs_exist_ok=True,ignore=_ignorepath(ignorelists,namespace_src, namespace_dst, purge=purge),copy_function=filtercopy(ignore_old=ignore_old,_=_))
        return _[0]
    elif path.isfile(src):
        filtercopy(ignore_old=ignore_old,_=_)(src,dst)
        return _[0]
    else: 
        print(Red(f"Updata failed: {dst} \nBecause: \"{src}\" is not a directory or a file.\n"))
        return False

def _ignorepath(pathlists:dict[str, list], namespace_src:str, namespace_dst:str, purge:bool = False) -> callable:
    def _ignore(current_dirname:str, src_filenames:list) -> set:
        keep_set:set[str] = set(src_filenames)
        if pathlists == {} or pathlists is None:
            pass
        else:
            delete_set:set[str] = set()
            modify_set:set[str] = set()
            add_set:set[str] = set()
            ignore_set:set[str] = set()
            
            #fn_filter(names, pattern)
            dirname:str
            filename:str
            
            for path_D in pathlists["D"]:
                path_D:str = path_D[0]
                path_D = path.join(namespace_src,path_D)
                dirname, filename = path.split(path_D)
                if fn_filter([current_dirname], dirname) or dirname == namespace_src:
                    names_set:set = set(fn_filter(src_filenames, filename))
                    delete_set.update(names_set)
                    if not names_set and (not dirname == namespace_src): print(Yellow(f"Warning : There were no results found for {filename} in \"{dirname}\"."))

            for path_M in pathlists["M"]:
                path_M:str = path_M[0]    
                path_M = path.join(namespace_src,path_M)
                #assert is_valid_pathname(path_M)
                dirname, filename = path.split(path_M)
                if fn_filter([current_dirname], dirname) or dirname == namespace_src:
                    names_set:set = set(fn_filter(src_filenames, filename))
                    modify_set.update(names_set)
                    if not names_set and (not dirname == namespace_src): print(Yellow(f"Warning : There were no results found for {filename} in \"{dirname}\"."))

            for path_A in pathlists["A"]:
                path_A:str = path_A[0].strip('\\')
                add_path:str = path.join(namespace_src ,path_A)
                #assert is_valid_pathname(add_path)
                if isparent_dir(current_dirname, add_path):
                    filename = get_top_dirname(add_path.replace(current_dirname,""))
                    if filename not in src_filenames : add_set.add(filename)
            
            for path_R in pathlists["R"]:
                rename_src_dir, rename_src_file = path.split(path_R[0].strip('\\'))
                rename_dst_dir, rename_dst_file = path.split(path_R[1].strip('\\'))
                rename_src_path = path.join(namespace_src, path_R[0].strip('\\'))
                rename_dst_path = path.join(namespace_dst, path_R[1].strip('\\'))
                #assert is_valid_pathname(rename_src_path) and is_valid_pathname(rename_dst_path)
                
                if fn_filter([current_dirname], path.dirname(rename_src_path)):
                    pathlists_for_rename:dict[str, list] = {'R':[],'M':[],'D':[],'A':[]}           
                    pathlists_for_rename['R'] = [(x.replace(path_R[0],"").strip('\\') if isparent_dir(path_R[0],x) else '', y.replace(path_R[1],"").strip('\\') if isparent_dir(path_R[1],y) else '') for (x,y) in pathlists['R']]
                    pathlists_for_rename['R'] = [x for x in pathlists_for_rename['R'] if x != ('','')]
                    
                    pathlists_for_rename['M'] = [tuple([x[0].replace(path_R[1],"").strip('\\')]) if isparent_dir(path_R[1],x[0]) else '' for x in pathlists['M']]
                    pathlists_for_rename['M'] = [x for x in pathlists_for_rename['M'] if x != ('')]

                    pathlists_for_rename['D'] = [tuple([x[0].replace(path_R[1],"").strip('\\')]) if isparent_dir(path_R[1],x[0]) else '' for x in pathlists['D']]
                    pathlists_for_rename['D'] = [x for x in pathlists_for_rename['D'] if x != ('')]

                    pathlists_for_rename['A'] = [tuple([x[0].replace(path_R[1],"").strip('\\')]) if isparent_dir(path_R[1],x[0]) else '' for x in pathlists['A']]
                    pathlists_for_rename['A'] = [x for x in pathlists_for_rename['A'] if x != ('')]

                    ignore_set.add(rename_src_file)
                    keep_set.discard(rename_src_file)
                    copydata(rename_src_path, rename_dst_path,ignorelists=pathlists_for_rename, purge=True,namespace_src=rename_src_path,namespace_dst=rename_dst_path)
                    print(Orange("Rename: \"{}\" \n -> \"{}\"\n".format(path.relpath(rename_src_path,current), path.relpath(rename_dst_path,current))))

                keep_renamed_path:str = path.join(namespace_src, rename_dst_dir).strip('\\')
                if fn_filter([current_dirname], keep_renamed_path):
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
            print(Grey(f"Ignore src: {path.relpath(path.join(current_dirname,dele),current)}"))
        for mod in modify_set:
            print(Cyan(f"Skip src: {path.relpath(path.join(current_dirname,mod),current)}"))
        for add in add_set:
            print(Blue(f"Keep: {path.relpath(path.join(path_dst,add),current)}"))

        return ignore_set
    return _ignore

def update(pre_ver:str,ver:str) -> None:
    def set_modify_list(modify_path:str) -> dict[str, list]:
        #R:rename, #M:modify, D:delete, A:add
        output:dict[str, list] = {'R':[],'M':[],'D':[],'A':[]}

        #Obtaining the paths of files will be modified.
        if not path.exists(modify_txt := path.join(modify_path, "Modify.txt")):
            print(Yellow(f"Warning: \"Modify.txt\" in {ver[1:]} does not exist, it will be added."))
            if not path.exists(path.dirname(modify_txt)): 
                makedirs(path.dirname(modify_txt))
            with open(modify_txt,"w"): 
                return None

        with open(modify_txt,"r") as r:
            key:str
            paths:str
            for i in r.readlines():
                if i.startswith('#'): 
                    continue
                i = i.strip().replace("/","\\").split(':')
                if (key:=i[0]) not in output.keys(): 
                    continue
                paths = i[1].split(',')
                if key in ('A','R','M') and not all(map(is_valid_pathname,paths)): 
                    print(Yellow(f"Warning : \"{paths}\" is not a vaild path name."))
                    continue
                output[key].append(tuple(map(lambda x:x.strip('\\'), paths)))
        return output

    src:str = path.join(current, "battlecats" + pre_ver)
    dst:str = path.join(current, "battlecats" + ver )
    
    modify_path:str = path.join(current, r"battlecats\vers", ver[1:])
    modify_list:dict[str, list] = set_modify_list(modify_path)

    #Copy files that not in ignore list and not in modify list.
    copydata(src+"\\assets", dst+"\\assets", ignorelists=modify_list, namespace_src=src, namespace_dst=dst, purge=True)
    
    #Copy files from the path "battlecats/vers/{ver}".
    if modify_list is None or modify_list == {}:
        return
    for MA in modify_list["M"] + modify_list["A"]:
        s:str = path.join(modify_path, path.basename(MA[0]))
        d:str = path.join(dst,MA[0])
        copydata(s,d,ignorelists=modify_list, purge=True,namespace_src=src,namespace_dst=dst)
    for D in modify_list['D']:
        delete(path.join(dst, D[0]))

def main():
    older_vers = ["", "_1.16.5", "_1.16.1", "_1.14.4", "_1.12.2", "_1.10.2", "_1.8.9"]
    vers = ["", "_1.17.1", "_1.18.2", "_1.19.2", "_1.19.3", "_1.19.4", "_1.20.1", "_1.20.2", "_1.20.4", "_1.20.6","_1.21.1","_1.21.3","_24w44a"]
    #resource_ver = {"1.8.9":1, "1.10.2":2, "1.12.2":3, "1.14.4":4, "1.16.1":5, "1.16.5":6, "1.17.1":7, "1.18.2":8, "1.19.2":9, "1.19.3":12, "1.19.4":13, "1.20.1":15, "1.20.2":18, "1.20.4":22, "1.20.6":32, "1.21":34, "1.21.2":39}
    #locks = threading.Lock()

    def update_older() -> None:
        #for i in range(1,2,1): 
        for i in range(1,len(older_vers),1):
            print(Strong('-'*25 + older_vers[i].replace('_','') + '-'*25))
            update(older_vers[i-1],older_vers[i])

    def update_newer() -> None:
        #for i in range(1,2,1): 
        for i in range(1,len(vers),1): 
            print(Strong('-'*25 + vers[i].replace('_','') + '-'*25))
            update(vers[i-1],vers[i])

    #older = threading.Thread(target=update_older)
    #older.start()

    update_older()
    update_newer()

if __name__ == '__main__':
    start_time = currenttime()
    main()
    print("\nFinish.")
    print("runtime: %s seconds" % (currenttime() - start_time))
    #input("Press Enter to continue...")