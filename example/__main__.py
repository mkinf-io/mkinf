import sys
import os
from streamlit.web import cli as stcli

def main():
    sys.argv = ["streamlit", "run", os.path.join(os.path.dirname(__file__), "view.py")]
    sys.exit(stcli.main())

if __name__ == "__main__":
    main()

