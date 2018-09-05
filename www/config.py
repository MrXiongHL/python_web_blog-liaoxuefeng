'''
Created on 2018-8-29

@author: 27136
'''

import config_default

class Dict(dict):
    def __init__(self,names=(),values=(),**kw):
        super(Dict,self).__init__(**kw)
        for k,v in zip(names,values):
            print('zip:%s=>%s'%(str(k),str(v)))
            self[k] = v
    
    def __getattr__(self,key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r'Dict has not attribute as:%s'%key)
    
    def __setattr__(self,key,value):
        self[key] = value

def merge(default,override):
    r = {}
    for k,v in default.items():
        if k in override:
            if isinstance(v, dict):
                r[k] = merge(v, override[k])
            else:
                r[k] = override[k]
        else:
            r[k] = v
    return r

def toDict(d):
    md = Dict()
    for k,v in d.items():
        md[k] = toDict(v) if isinstance(v, dict) else v
    
    return md


        
configs = config_default.configs

try:
    import config_override
    configs = merge(configs, config_override.configs)
except ImportError:
    pass

configs = toDict(configs)

if __name__ == '__main__':
        
    configs = config_default.configs
    
    try:
        import config_override
        configs = merge(configs, config_override.configs)
    except ImportError:
        pass
    
    configs = toDict(configs)














        