import re, threading
from ComSpec import *
from lib.consts import PLUGIN_DISPLAY_COMMUNICATION

class CCommandParser(object):
    
    def __init__(self, buffer, proxy, client=False, addr=None):
        '''
        @param buffer: input will be read from this object.
        @type buffer: L{CLineSynchBuffer<SynchLineBuffer.CSynchLineBuffer>}
        
        @param proxy: proxy object to handle received commands
        
        @param client: True if used from worker, False if used from manager
            Accepted syntax of protocol depends on it
        
        @param addr: identifier of connection
        '''
        
        self.addr = addr
        self.buffer = buffer
        self.proxy = proxy
        self.run = True
        self.client = client
        
        if client:
            self.firstline = FIRST_LINE_PLUGIN
        else:
            self.firstline = FIRST_LINE_MAIN
        
        self.paramline = PARAM_LINE
        self.emptyline = EMPTY_LINE
        
        threading.Thread(target = self._mainloop).start()
    
    def Stop(self):
        '''
        Stop reading from socket, thread will be stopped asynchronously
        '''
        self.buffer.Close()
        self.run = False
    
    def _mainloop(self):
        '''
        main cycle of parsing commands from socket
        runs in separate thread
        '''
        self.state = 'firstline'
        
        try:
            params = {}
            data = []
            while self.run:
                line = self.buffer.Read()
                if line is None:
                    self.Stop()
                    break
                
                if PLUGIN_DISPLAY_COMMUNICATION and self.client:
                    print `line`
                
                if self.state == 'firstline':
                    if self.emptyline.match(line):
                        continue
                    match = self.firstline.match(line)
                    if match is None:
                        if self.proxy.Error(self.addr):
                            self.state = 'firstline'
                        else:
                            break
                    else:
                        command = match.groupdict()
                        self.state = 'params'
                
                elif self.state == 'params':
                    if self.emptyline.match(line):
                        self.state = 'data'
                        continue
                    match = self.paramline.match(line)
                    if match is None:
                        if self.proxy.Error(self.addr):
                            self.state = 'firstline'
                        else:
                            break
                    else:
                        keyval = match.groupdict()
                        params[keyval['key']] = keyval['value']
                        
                elif self.state == 'data':
                    if self.emptyline.match(line):
                        self.state = 'firstline'
                        self.proxy.Command(command, params, data, self.addr)
                        data = []
                        params = {}
                    else:
                        data.append(line)
                
        finally:
            self.run = None
            self.proxy.Stopped(self.addr)
