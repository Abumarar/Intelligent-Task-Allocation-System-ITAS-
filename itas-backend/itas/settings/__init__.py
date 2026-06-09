import os

if os.environ.get("RENDER"):
    from .production import *
else:
    from .development import *
