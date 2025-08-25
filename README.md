### install
```pip install -r requirements.txt```

### dev
```python -m src.main```

### compile
```nuitka --standalone --onefile --python-flag=no_site --enable-plugin=no-qt --follow-imports src/main.py```

```
nuitka --standalone --onefile --enable-plugin=no-qt --follow-imports --include-data-dir=assets=assets --output-dir=dist --windows-disable-console src/main.py
```

