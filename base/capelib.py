# Common routines needed for Cape tool chain

def succinctify(value):
    def helper(x):
        x = x[:x.index(')')] if ')' in x else x
        return x.lower().strip().replace(' ', '_').replace('_(', '_').replace('._','_')
    if isinstance(value, str):
        return helper(value)
    else:
        return list(map(helper,value))
