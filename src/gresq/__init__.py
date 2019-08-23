import sys

def run_dashboard():
    from .dashboard import main
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
