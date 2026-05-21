import subprocess
import webbrowser
import time
import sys
import os

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(sys.executable 
        if getattr(sys, 'frozen', False) else __file__))
    
    app_path = os.path.join(base_dir, 'app.py')
    python_path = os.path.join(base_dir, '_internal', 'python.exe')
    
    if not os.path.exists(python_path):
        python_path = sys.executable
    
    subprocess.Popen(
        [python_path, app_path],
        cwd=base_dir,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    
    time.sleep(3)
    webbrowser.open('http://127.0.0.1:5000')