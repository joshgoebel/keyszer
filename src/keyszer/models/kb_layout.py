import dbus


bus = dbus.SessionBus()
dbus_obj = bus.get_object('org.freedesktop.DBus', '/')
dbus_iface = dbus.Interface(dbus_obj, 'org.freedesktop.DBus')
names = dbus_iface.ListNames()

shell_names = [name for name in names if ':' not in name]
print('#################################')
print('Available objects NOT containing ":":')
for name in shell_names:
    print(name)
print('#################################')

