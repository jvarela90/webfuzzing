# Test de imports principales
python -c "
try:
    import aiohttp
    print('✅ aiohttp OK')
    import flask
    print('✅ flask OK')  
    import requests
    print('✅ requests OK')
    import pandas
    print('✅ pandas OK')
    import plotly
    print('✅ plotly OK')
    import sqlalchemy
    print('✅ sqlalchemy OK')
    from core.fuzzing_engine import *
    print('✅ fuzzing_engine OK')
    print('🎉 TODAS LAS DEPENDENCIAS FUNCIONAN')
except ImportError as e:
    print('❌ ERROR:', e)
"