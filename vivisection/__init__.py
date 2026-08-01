'''
VivisectION core
'''
from vivisection.emutils import NinjaEmulator

class NoWorkspace(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __repr__(self):
        return "NoWorkspace: %r" % self.msg

class VivisectION:
    '''
    '''
    def __init__(self, vw=None):
        self.vw = None
        self.nemu = None

        if vw:
            self.setVw(vw)
            self.resetEmu()

    def setEmuOpts(self, start=None, verbose=False, fakePEB=False, hookfunctionsbyname=False, **kwargs):
        kwargs['start'] = start
        kwargs['verbose'] = verbose
        kwargs['fakePEB'] = fakePEB
        kwargs['hookfunctionsbyname'] = hookfunctionsbyname
        self.emuopts = kwargs

    def setEmuOpt(self, key, val):
        self.emuopts[key] = val

    def setVw(self, vw):
        self.vw = vw

    def resetEmu(self, emu=None):
        if not self.vw:
            raise NoWorkspace("no workspace loaded")

        self.nemu = NinjaEmulator(emu, vw=self.vw)