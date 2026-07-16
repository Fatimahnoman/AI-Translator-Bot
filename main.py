"""
TranslateHub — Vercel Entry Point
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ["CHAINLIT_APP_ROOT"] = os.path.dirname(os.path.abspath(__file__))

from chainlit.utils import mount_chainlit

app = mount_chainlit("./trans-agent.py")
