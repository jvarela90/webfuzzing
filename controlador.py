python -c "
import sys
print('Python:', sys.version)
try:
    import aiohttp
    print('✅ aiohttp OK')
except ImportError as e:
    print('❌ aiohttp FALTA:', e)

try:
    from core.fuzzing_engine import *
    print('✅ fuzzing_engine OK')
except ImportError as e:
    print('❌ fuzzing_engine ERROR:', e)

try:
    import flask
    print('✅ flask OK')
except ImportError as e:
    print('❌ flask ERROR:', e)
"