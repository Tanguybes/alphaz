def singleton(cls):
    print('\nCLASS %s\n'%str(cls))
    instance = None
    def ctor(*args, **kwargs):
        nonlocal instance
        if not instance:
            instance = cls(*args, **kwargs)
        return instance
    return ctor

"""class AlphaSingleton:
    class __OnlyOne:
        def __init__(self, arg):
            self.val = arg
        def __str__(self):
            return repr(self) + self.val

    instance = None

    def __init__(self, arg):
        if not AlphaSingleton.instance:
            AlphaSingleton.instance = AlphaSingleton.__OnlyOne(arg)
            print('   hey')
        else:
            AlphaSingleton.instance.val = arg
            print('   ooh   ')

    def __getattr__(self, name):
        return getattr(self.instance, name)"""