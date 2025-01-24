import os
import sys
import shutil
import platform
import json
from pathlib import Path

# Add parent directory to Python path if running as script
if __name__ == "__main__":
    parent_dir = Path(__file__).parent.parent
    if str(parent_dir) not in sys.path:
        sys.path.append(str(parent_dir))

FONT_FILES = [
    "MedievalSharp-Regular.ttf",
    "UnifrakturMaguntia-Regular.ttf"
]

def get_app_data_dir():
    system = platform.system()
    if system == "Windows":
        return Path(os.getenv('LOCALAPPDATA')) / "AI-DM"
    elif system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "AI-DM"
    else:  # Linux/BSD
        return Path.home() / ".config" / "ai-dm"

def get_first_run_flag_path():
    app_data_dir = get_app_data_dir()
    app_data_dir.mkdir(parents=True, exist_ok=True)
    return app_data_dir / "first_run.json"

def check_first_run():
    flag_file = get_first_run_flag_path()
    return not flag_file.exists()

def mark_first_run_complete():
    flag_file = get_first_run_flag_path()
    with flag_file.open('w') as f:
        json.dump({"first_run": False}, f)

def get_system_font_dir():
    system = platform.system()
    if system == "Windows":
        return Path(os.getenv('WINDIR')) / 'Fonts'
    elif system == "Darwin":
        return Path.home() / "Library" / "Fonts"
    else:  # Linux/BSD
        return Path.home() / ".local" / "share" / "fonts"

def install_fonts():
    script_dir = Path(__file__).parent.parent.resolve()
    fonts_src = script_dir / "assets" / "fonts"
    fonts_dest = get_system_font_dir()
    
    fonts_dest.mkdir(parents=True, exist_ok=True)
    
    installed = []
    for font in FONT_FILES:
        src = fonts_src / font
        dest = fonts_dest / font
        
        if not src.exists():
            raise FileNotFoundError(f"Font file missing: {src}")
            
        if not dest.exists():
            shutil.copy(src, dest)
            installed.append(font)
    
    if platform.system() in ["Linux", "Darwin"]:
        os.system("fc-cache -f -v")
    
    return installed

def main():
    print("=== Medieval Font Installer ===")
    try:
        if check_first_run():
            installed = install_fonts()
            mark_first_run_complete()
            print(f"Installed fonts: {', '.join(installed)}")
            print("First time setup complete!")
        else:
            print("Fonts already installed previously")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
