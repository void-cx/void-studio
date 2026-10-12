"""Pack-Beschreibungen einheitlich formatieren: python3 themes/fmt.py"""
import glob, json, os


def dump(o, ind=0):
    p = '  ' * ind
    if isinstance(o, dict) and o:
        return '{\n' + ',\n'.join(f'{p}  {json.dumps(k, ensure_ascii=False)}: {dump(v, ind + 1)}' for k, v in o.items()) + f'\n{p}}}'
    if isinstance(o, list) and any(isinstance(x, (list, dict)) for x in o):
        return '[\n' + ',\n'.join(f'{p}  {dump(v, ind + 1)}' for v in o) + f'\n{p}]'
    return json.dumps(o, ensure_ascii=False)


for f in sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), '*.json'))):
    data = json.load(open(f, encoding='utf-8'))
    with open(f, 'w', encoding='utf-8') as out:
        out.write(dump(data) + '\n')
