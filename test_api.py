import json

data: dict

with open("test_cpu.json", 'r') as json_file:
    data = json.load(json_file)


print(data)