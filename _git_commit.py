import subprocess, os
os.chdir(r'c:\Users\Usuario\OneDrive\Desktop\S.I.D.I.C')

# Remove temp files
for f in ['_git_check.py', '_git_status.txt', 'test_output.txt', 'test_results.txt']:
    try:
        os.remove(f)
        print(f"Removed: {f}")
    except FileNotFoundError:
        pass

# Unstage and re-add without temp files
subprocess.run(['git', 'reset', 'HEAD', '--', '_git_check.py', '_git_status.txt', 'test_output.txt', 'test_results.txt'], capture_output=True)
subprocess.run(['git', 'add', '-A'])

# Commit
r = subprocess.run(['git', 'commit', '-m', 'feat: S.I.D.I.C v2.0 - Complete rebuild with Clean Architecture\n\n- Domain layer: enums, models, services, protocols\n- Application layer: DTOs, use cases\n- Infrastructure: GIS readers, exporters, SQLite persistence\n- Presentation: PyQt6 MVVM, dark police theme\n- Config: JSON-based crime categorization\n- Tests: 207 unit tests (pytest)\n- Entry points: GUI and CLI'], capture_output=True, text=True)
with open('_commit_result.txt', 'w') as f:
    f.write(f"STDOUT:\n{r.stdout}\n\nSTDERR:\n{r.stderr}\n\nRC: {r.returncode}\n")
