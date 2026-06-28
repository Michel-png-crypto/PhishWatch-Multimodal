import os
p=None
with open('.env','r',encoding='utf-8') as f:
    for line in f:
        print('LINE REPR:',repr(line))
        if line.strip().startswith('VIRUSTOTAL_API_KEY'):
            parts=line.strip().split('=',1)
            print('PARTS:',parts)
            if len(parts)==2:
                p=parts[1].strip().strip('"').strip("'")
                break
print('PARSED:',p)
