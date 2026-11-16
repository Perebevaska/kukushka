import sys
import pandas as pd
def env_report():
    return {"python":f"{sys.version_info.major}.{sys.version_info.minor}","pandas":pd.__version__}
env_report()
