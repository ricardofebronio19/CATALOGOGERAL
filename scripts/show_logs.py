import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import app
p = app.APP_DATA_PATH
print('APP_DATA_PATH=', p)
for name in ['task_link_images.log','task_import.log','task_import.log','task_import.log']:
    path = os.path.join(p, name)
    if os.path.exists(path):
        print('\n---', name, '---')
        with open(path, 'rb') as f:
            data = f.read()
        try:
            text = data.decode('utf-8')
        except Exception as e:
            print('Decoding with utf-8 failed:', e)
            text = data.decode('latin-1', errors='replace')
        print('\n'.join(text.splitlines()[-200:]))
    else:
        print('\n---', name, 'not found ---')
