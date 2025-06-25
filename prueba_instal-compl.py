python -c "
print('🧪 TESTING COMPLETE SYSTEM...')
print('=' * 50)

# Test 1: Core imports
try:
    import aiohttp, flask, requests, sqlalchemy
    print('✅ Core web dependencies OK')
except ImportError as e:
    print('❌ Core dependencies FAILED:', e)

# Test 2: Data processing
try:
    import pandas, numpy, plotly
    print('✅ Data processing dependencies OK')
except ImportError as e:
    print('❌ Data processing FAILED:', e)

# Test 3: Security tools
try:
    import beautifulsoup4, selenium, cryptography
    print('✅ Security tools dependencies OK')
except ImportError as e:
    print('❌ Security tools FAILED:', e)

# Test 4: Your modules
try:
    from core.fuzzing_engine import *
    print('✅ Fuzzing engine imports OK')
except ImportError as e:
    print('❌ Fuzzing engine FAILED:', e)

print('=' * 50)
print('🎉 DEPENDENCY TEST COMPLETED')
"