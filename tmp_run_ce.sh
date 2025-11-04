#!/bin/bash
python - <<'PY'
from importlib.machinery import SourceFileLoader
mod = SourceFileLoader('ce','/tmp/continuous_extract.py').load_module()
mod.MAX_WORKERS = 2
with open('/tmp/continuous_extract.pid','w') as f: f.write(str(os.getpid()))
try:
    mod.main()
except SystemExit:
    pass
PY
