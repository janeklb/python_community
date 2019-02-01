"""VPN Extension

Connect or disconnect from a network manager VPN profile"""


import dbus
import time
from collections import namedtuple
from albertv0 import *
from shutil import which


__iid__ = "PythonInterface/v0.2"
__prettyname__ = "VPN"
__version__ = "1.0"
__trigger__ = "vpn "
__author__ = "janeklb"
__dependencies__ = ['nmcli']


iconPath = iconLookup('network-wireless')
if not iconPath:
    iconPath = ":python_module"

VPNConnection = namedtuple('VPNConnection', ['name', 'connected'])

class Timer:    
    def __init__(self, label):
        self.label = label

    def __enter__(self):
        self.start = time.clock()
        return self

    def __exit__(self, *args):
        self.end = time.clock()
        self.interval = self.end - self.start
        info('%s took %.03f seconds' % (self.label, self.interval))


bus = dbus.SystemBus()
service_name = "org.freedesktop.NetworkManager"
proxy = bus.get_object(service_name, "/org/freedesktop/NetworkManager/Settings")
settings = dbus.Interface(proxy, "org.freedesktop.NetworkManager.Settings")
connection_paths = settings.ListConnections()


def getVPNConnections():
    for path in connection_paths:
        with Timer('bus.get_object'):
            con_proxy = bus.get_object(service_name, path)
        with Timer('dbus.Interface'):
            settings_connection = dbus.Interface(con_proxy, "org.freedesktop.NetworkManager.Settings.Connection")
        with Timer('settings_connection.GetSettings()'):
            config = settings_connection.GetSettings()
        connection = config['connection']
        if connection['type'] == 'vpn':
            yield VPNConnection(
                name=connection['id'],
                connected='timestamp' in connection
            )    


def buildItem(con):
    name = con.name
    command = 'down' if con.connected else 'up'
    text = f'Connect to {name}' if command == 'up' else f'Disconnect from {name}'
    commandline = ['nmcli', 'connection', command, 'id', name]
    return Item(
        id=f'vpn-{command}-{name}',
        text=name,
        subtext=text,
        icon=iconPath,
        completion=name,
        actions=[ ProcAction(text=text, commandline=commandline) ]
    )


def initialize():
    if which('nmcli') is None:
        raise Exception("'nmcli' is not in $PATH")


def handleQuery(query):
    if query.isValid and query.isTriggered:
        with Timer('getVPNConnections'):
            connections = getVPNConnections()
        if query.string:
            connections = [ con for con in connections if query.string.lower() in con.name.lower() ]
        return [ buildItem(con) for con in connections ]
    return []

