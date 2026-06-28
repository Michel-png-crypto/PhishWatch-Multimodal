import os
print('CWD:', os.getcwd())
print('__file__ dir:', os.path.dirname(__file__))
print('.env exists cwd:', os.path.exists('.env'))
print('.env exists same dir:', os.path.exists(os.path.join(os.path.dirname(__file__), '.env')))
try:
    with open('.env','r',encoding='utf-8') as f:
        print('.env content (cwd):')
        print(f.read())
except Exception as e:
    print('cannot read .env in cwd:', e)
try:
    with open(os.path.join(os.path.dirname(__file__), '.env'),'r',encoding='utf-8') as f:
        print('.env content (file dir):')
        print(f.read())
except Exception as e:
    print('cannot read .env in file dir:', e)
