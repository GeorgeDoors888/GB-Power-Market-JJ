from importlib.machinery import SourceFileLoader
import os
mod = SourceFileLoader('ce','/tmp/continuous_extract.py').load_module()
mod.MAX_WORKERS = 2
with open('/tmp/continuous_extract.pid','w') as f:
    f.write(str(os.getpid()))
mod.main()
