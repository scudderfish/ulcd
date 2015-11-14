#!/usr/bin/env python
import pexpect,sys
pexpect.run('sitecopy -u wipy')
a=pexpect.spawn('telnet 192.168.1.1')
a.logfile=sys.stdout
a.expect('Login as:')
a.sendline('micro')
a.expect('assword:')
a.sendline('python')
a.expect('>>>')
a.sendcontrol('d')
a.expect('>>>')
a.sendline('import ulcd\r')
a.expect('>>>')
a.sendline('ulcd.lcd().test()\r')
a.expect('>>>')
