
# jurigged-for-dl

[Jurigged](https://github.com/breuleux/jurigged) is a Python library that lets you hot-patch running code — change a function or method in your editor, save the file, and the live process picks it up immediately without restarting.

![sample demo](https://user-images.githubusercontent.com/599820/113785377-ffab1e80-9704-11eb-9c82-6d866c9087a6.gif)

This fork extends jurigged with additions aimed at **deep learning workflows**, where restarting a process to tweak a training step is expensive.

---

## What was added

### Jupyter / IPython cell hot-swap

The main addition is a Jupyter/IPython extension that patches functions and classes **in-place** when you re-run a notebook cell. Existing references (e.g. a PyTorch training loop that already holds a reference to `train_step`) are updated automatically — no restart needed.

#### Install

```bash
git clone https://github.com/edujbarrios/jurigged-for-dl.git
cd jurigged-for-dl
pip install -e ".[notebook]"
```

If you only need upstream Jurigged (without the additions in this fork), install it directly with:

```bash
pip install "jurigged[notebook]"
```

#### Usage

Load the extension once at the top of your notebook:

```python
%load_ext jurigged
```

After that, re-running any cell that redefines a top-level function or class will patch the previous object in-place and rebind the name back to the original identity. All existing references across the notebook continue to point to the same object, now with the updated code.

#### Programmatic API

You can also enable and disable the hot-swap behaviour from Python directly:

```python
from jurigged.notebook import enable, disable, patch_namespace

# Enable hot-swap for the current IPython session
enable()

# Disable it
disable()

# Or use patch_namespace manually to patch a dict of objects
patch_namespace(before_snapshot, after_snapshot, module_name="__main__")
```

`patch_namespace` compares two namespace snapshots and patches any functions or classes that were redefined between them, keeping object identity intact.

#### Why this matters for DL

In a typical deep learning loop the trainer holds direct references to model methods, loss functions, and callbacks. With `%autoreload` those references go stale because a full module reload creates new objects. With this extension the **same objects are mutated**, so every part of your code that already holds a reference sees the new behaviour immediately.
