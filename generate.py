import subprocess

if __name__ == "__main__":

    subprocess.run([
            "pyinstaller",
            "--noconfirm",
            "--clean",
            "--name", "sr5tools",
            "--additional-hooks-dir", ".",
            "--onefile",
            "standalone.py"
    ], check=True)
