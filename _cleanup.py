import subprocess, os
os.chdir(r'c:\Users\Usuario\OneDrive\Desktop\S.I.D.I.C')

# Remove temp files
for f in ['_git_commit.py', '_commit_result.txt']:
    try:
        os.remove(f)
    except FileNotFoundError:
        pass

subprocess.run(['git', 'add', '-A'])
r = subprocess.run(['git', 'commit', '-m', 'chore: remove temporary script files'], capture_output=True, text=True)
print(r.stdout)
print(r.returncode)
