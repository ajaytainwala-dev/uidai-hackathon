
import os
import json
import shutil

# Configuration
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BUILD_DIR = os.path.join(ROOT_DIR, "docs")
SRC_DIR = "aadhaar_analytics"
ENTRYPOINT = "aadhaar_analytics/dashboard/app.py"

# Files to ignore
IGNORE_DIRS = {"__pycache__", ".ipynb_checkpoints", ".git", ".venv", "env", "venv"}
IGNORE_EXTS = {".pyc", ".pyo", ".pyd"}

def get_file_map():
    file_map = {}
    
    # 1. Walk the source directory
    abs_src = os.path.join(ROOT_DIR, SRC_DIR)
    for root, dirs, files in os.walk(abs_src):
        # Filter directories
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            _, ext = os.path.splitext(file)
            if ext in IGNORE_EXTS:
                continue
                
            abs_path = os.path.join(root, file)
            # Relative path from project root (for virtual fs key)
            rel_path = os.path.relpath(abs_path, ROOT_DIR).replace("\\", "/")
            
            # For Stlite, we can serve files or inline them. 
            # Inlining 22MB CSV is bad for HTML size. 
            # We will use "url" loading which fetches them relative to the index.html.
            # But the files must exist in the build dir.
            file_map[rel_path] = {
                "url": rel_path,
            }
            
    return file_map

def build():
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
    os.makedirs(BUILD_DIR)
    
    print(f"Building to {BUILD_DIR}...")
    
    # Copy source code
    dest_src = os.path.join(BUILD_DIR, SRC_DIR)
    shutil.copytree(os.path.join(ROOT_DIR, SRC_DIR), dest_src, 
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".ipynb_checkpoints"))

    # Copy Data Folders
    data_dirs = ["api_data_aadhar_enrolment", "api_data_aadhar_demographic", "api_data_aadhar_biometric"]
    for d in data_dirs:
        src = os.path.join(ROOT_DIR, d)
        dst = os.path.join(BUILD_DIR, "data", d)
        if os.path.exists(src):
            print(f"Copying {d} to {dst}...")
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns(".ipynb_checkpoints"))
        else:
            print(f"WARNING: Data source {src} not found!")

    # Generate Manifest for JS
    manifest = {}
    web_dir = os.path.join(BUILD_DIR, "web")
    if not os.path.exists(web_dir):
        os.makedirs(web_dir)
        
    for d in data_dirs:
        dst = os.path.join(BUILD_DIR, "data", d)
        if os.path.exists(dst):
             files = [f for f in os.listdir(dst) if f.endswith('.csv')]
             manifest[d] = files
    
    with open(os.path.join(web_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f)
    
    # Generate File Mapping
    file_map = get_file_map()
    
    # Create index.html
    # We use the Stlite mounting mechanism
    
    html_content = f"""
<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no" />
    <title>Aadhaar Analytics</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@stlite/mountable@0.53.0/build/stlite.css" />
  </head>
  <body>
    <div id="root"></div>
    <script src="https://cdn.jsdelivr.net/npm/@stlite/mountable@0.53.0/build/stlite.js"></script>
    <script>
      stlite.mount(
        {{
          requirements: ["streamlit", "pandas", "plotly"],
          entrypoint: "{ENTRYPOINT}",
          files: {json.dumps(file_map, indent=2)}
        }},
        document.getElementById("root")
      );
    </script>
  </body>
</html>
    """
    
    with open(os.path.join(BUILD_DIR, "index.html"), "w", encoding='utf-8') as f:
        f.write(html_content)
        
    print("Build Complete! The 'docs' folder is ready for GitHub Pages.")

if __name__ == "__main__":
    build()
