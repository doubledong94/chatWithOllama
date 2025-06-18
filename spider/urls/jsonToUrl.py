import json


# 递归遍历所有键值对
def recursive_print(data, indent=0):
    if isinstance(data, dict):
        for key, value in data.items():
            print(' ' * indent + str(key) + ':')
            recursive_print(value, indent + 2)
    elif isinstance(data, list):
        for item in data:
            recursive_print(item, indent + 2)
    else:
        print(' ' * indent + str(data))

# 递归遍历所有键值对,将键值为type的所有枚举值列出来
def recursive_enum(data, enum_values=None):
    if enum_values is None:
        enum_values = set()

    if isinstance(data, dict):
        for key, value in data.items():
            if key == 'type' and isinstance(value, str) and value == "article":
                enum_values.add(data['path'])
            recursive_enum(value, enum_values)
    elif isinstance(data, list):
        for item in data:
            recursive_enum(item, enum_values)

    return enum_values


if __name__ == '__main__':
    json_data  = json.load(open('StoreKit.json', 'r', encoding='utf-8'))
    print('\n'.join(recursive_enum(json_data)))
    json_data  = json.load(open('StoreKitTest.json', 'r', encoding='utf-8'))
    print('\n'.join(recursive_enum(json_data)))
    json_data  = json.load(open('AppStoreConnectAPI.json', 'r', encoding='utf-8'))
    print('\n'.join(recursive_enum(json_data)))
    json_data  = json.load(open('AppStoreServerAPI.json', 'r', encoding='utf-8'))
    print('\n'.join(recursive_enum(json_data)))
    json_data  = json.load(open('AppStoreServerNotifications.json', 'r', encoding='utf-8'))
    print('\n'.join(recursive_enum(json_data)))
