
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

---

## Use Cases

`jurigged-for-dl` is most useful when notebook-based deep learning work is already running and you need to keep momentum while refining Python code. It primarily hot-reloads Python functions, methods, classes, training logic, callbacks, and utility code so updates can apply at the next batch, next iteration, next epoch, or next function call without restarting the kernel.

### Notebook Iteration Workflows

In long Jupyter sessions, this is practical for rapid experimentation where restarting is costly:

- updating `train_step` logic while a PyTorch or Lightning run is active;
- iterating on validation/evaluation logic in CNN, VLM, or LLM notebooks;
- adjusting augmentation and preprocessing utility functions between experiments;
- tweaking sampling and scheduler utilities used during training loops;
- refining metrics and logging callbacks during active runs.

This is especially helpful when notebook state includes expensive setup, such as loaded tokenizers, cached datasets, precomputed features, dataloaders, and large GPU-resident models.

### Deep Learning & Fine-Tuning

Typical deep learning use cases include:

- changing loss behavior during CLIP or other VLM fine-tuning;
- iterating on PEFT/LoRA adapter training logic in HuggingFace Transformers;
- modifying diffusion training loops and callback behavior in Diffusers;
- adjusting reward shaping and evaluation code in RLHF-style notebook experiments;
- refining experiment control flow in long GPU sessions without reloading multi-GB checkpoints.

With distributed or optimized stacks (Accelerate, DeepSpeed, FSDP, DDP, `torch.compile`), hot-reload can still help at the Python orchestration layer, but behavior depends on how much logic is captured/compiled outside normal Python execution.

### What Persists Across Reloads

In most notebook workflows, the following typically survives while code definitions are patched:

- notebook variables and intermediate tensors already in memory;
- instantiated objects (models, trainers, callbacks, helper classes);
- loaded checkpoints and model/optimizer instances;
- GPU memory allocations already held by the process;
- dataloaders, dataset handles, and cached preprocessing state;
- long-running notebook sessions and their in-memory context;
- existing references that point to patched functions/classes.

Persistence does not guarantee semantic correctness after arbitrary code edits. If interfaces, invariants, or expected object structure change, you may still need to recreate parts of the runtime state.

### Typical Workflow Improvement

#### Without jurigged-for-dl

1. Stop training.
2. Restart kernel.
3. Reload checkpoints.
4. Rebuild dataloaders.
5. Re-run notebook setup.
6. Resume training.

#### With jurigged-for-dl

1. Edit a function, method, or class.
2. Re-run the notebook cell.
3. Continue training from the current runtime state.

### Known Limitations

- Changes to `__init__` do not retroactively rebuild already-instantiated objects.
- Structural `nn.Module` changes (new/removed submodules or parameter shapes) often require model recreation.
- Optimizer parameter groups can become stale after structural parameter changes.
- `torch.compile` graphs may need recompilation to reflect updated Python logic.
- JIT/traced modules are not guaranteed to reload correctly.
- Active stack frames are not rewritten mid-execution; changes apply on subsequent calls.
- In distributed or multiprocess setups (DDP/FSDP/DeepSpeed), additional coordination may be required to keep workers consistent.
- This tool does not mutate tensor state, optimizer internals, compiled graphs, or model parameter structure in place.

### What this is NOT

This is not live tensor surgery, automatic optimizer migration, universal compatibility magic, or guaranteed-safe mutation of arbitrary running training systems. It is a targeted way to patch Python-level training code during iterative notebook development.

For deep learning experimentation in notebooks, the main value is shorter iteration loops: keep expensive runtime state alive, patch Python logic in place, and continue from where the session already is.
