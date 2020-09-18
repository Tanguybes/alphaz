#from functools import wraps

#test_method_name = 'test_call'
"""class test(object):
    def __init__ (self, *args, **kwargs):
        # store arguments passed to the decorator
        self.args = args
        self.kwargs = kwargs

    def __call__(self, func):
        def test_call(*args, **kwargs):
            #the 'self' for a method function is passed as args[0]
            slf = args[0]

            # replace and store the attributes
            saved = {}
            for k,v in self.kwargs.items():
                if hasattr(slf, k):
                    saved[k] = getattr(slf,k)
                    setattr(slf, k, v)

            # call the method
            ret = func(*args, **kwargs)

            #put things back
            for k,v in saved.items():
                setattr(slf, k, v)

            return ret
        test_call.__doc__ = func.__doc__
        return test_call """

TEST_METHOD_NAME = "test_alpha_in"
def test(save=False, description=None, stop=True):
    def test_alpha_in(func):
        def test_wrapper(*args,**kwargs):
            return func(*args, **kwargs)

        if hasattr(func,'__name__'):
            test_wrapper.__name__ = func.__name__
        else:
            pass
        
        return test_wrapper
    return test_alpha_in

save_method_name = "save_method_result"  
def save(func):
    def save_method_result(*args, **kwargs):  
        get_return, get_name = False, False
        new_kwargs = {}
        args = list(args)
        #print('must-have arguments are:')
        """for i in args:
            print(i)   """       
        #print('optional arguments are:')
        for kw in kwargs.keys():
            #print( kw+'='+str( kwargs[kw] ) )
            if kw == "get_return":
                get_return = True
            elif kw == "get_name":
                get_name = True
            else:
                new_kwargs[kw] = kwargs[kw]

        return_save = AlphaSave.load(func.__name__)

        if get_return:
            return func(*args, **new_kwargs)
        elif get_name:
            return func.__name__
        else:
            return func(*args, **new_kwargs) == return_save
    return save_method_result




