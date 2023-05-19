import dbus


# Module to assess available GNOME Shell extensions


bus = dbus.SessionBus()
# Get the org.gnome.Shell.Extensions interface
proxy = bus.get_object("org.gnome.Shell.Extensions", "/org/gnome/Shell/Extensions")
# Alternate proxy that also seems to work:
# proxy = bus.get_object("org.gnome.Shell", "/org/gnome/Shell")
iface = dbus.Interface(proxy, "org.gnome.Shell.Extensions")
# # Retrieve the list of enabled extensions
extensions_dbus_dict = iface.ListExtensions()

# print()
# print("Printing extensions_dbus_dict contents, line by line:")
# print("######################################################")
# for k, v in extensions_dbus_dict.items():
#     print(f'{k}: {v}')


def dbus_to_py(obj):
    if isinstance(obj, dbus.ByteArray):
        return bytes(obj)
    elif isinstance(obj, dbus.String):
        return str(obj)
    elif isinstance(obj, dbus.Int16) or isinstance(obj, dbus.UInt16) \
            or isinstance(obj, dbus.Int32) or isinstance(obj, dbus.UInt32) \
            or isinstance(obj, dbus.Int64) or isinstance(obj, dbus.UInt64):
        return int(obj)
    elif isinstance(obj, dbus.Boolean):
        return bool(obj)
    elif isinstance(obj, dbus.Double):
        return float(obj)
    elif isinstance(obj, dbus.Array):
        return [dbus_to_py(elem) for elem in obj]
    elif isinstance(obj, dbus.Dictionary):
        return dict([(dbus_to_py(k), dbus_to_py(v)) for k, v in obj.items()])
    elif isinstance(obj, dbus.Struct):
        return tuple([dbus_to_py(elem) for elem in obj])
    elif isinstance(obj, dbus.Byte):
        return int(obj)
    else:
        return obj

# Assuming you have a D-Bus dictionary object named 'enabled_extensions'
# First, get the keys and values from the D-Bus dictionary object
extensions_dbus_keys = extensions_dbus_dict.keys()
extensions_dbus_values = extensions_dbus_dict.values()

# Next, convert the keys and values to Python objects
extensions_py_keys = [dbus_to_py(k) for k in extensions_dbus_keys]
extensions_py_values = [dbus_to_py(v) for v in extensions_dbus_values]

# Finally, create a Python dictionary from the keys and values
extensions_py_dict = dict(zip(extensions_py_keys, extensions_py_values))

# print()
# print("Printing extensions_py_dict contents, line by line:")
# print("######################################################")
# for k, v in extensions_py_dict.items():
#     print(f'{k}: {v}')

extensions_dct = {}
for k, v in extensions_py_dict.items():
    extensions_dct.update({k: {'uuid': v['uuid'], 'name': v['name'], 'state': v['state']}})
    # extension_info.update({k: {'name': v['name'], 'uuid': v['uuid'], 'state': v['state']}})
    # print(f"name: {v['name']}")
    # print(f"uuid: {v['uuid']}")
    # print(f"state: {v['state']}")
    # for _k, _v in v.items():
    #     print(f'    {_k}: {_v}')
    # print("########")

# state 1.0 == (enabled), state 2.0 == (disabled?), state 6.0 (disabled?)

print()
print("Printing extensions_dct contents, line by line:")
print("######################################################")
for k, v in extensions_dct.items():
    print(f'{k}: {v}')

print()
print("Printing only the keys (extension uuids) from extensions_dct, line by line:")
print("######################################################")
for e in extensions_dct:
    print(e)

print()
print("Printing the values attached to the keys for the GNOME extensions:")
print("######################################################")
print(extensions_dct['window-calls-extended@hseliger.eu'])
print(extensions_dct['xremap@k0kubun.com'])
