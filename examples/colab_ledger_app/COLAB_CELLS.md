# Mobile Colab Ledger App Cells

Copy these cells into Google Colab.

## 1. Setup

```python
from google.colab import drive
drive.mount("/content/drive")

!pip install usekit

from usekit import use
use.colab()
```

## 2. Generate and run the ledger app

Paste and run:

```text
examples/ledger_app/ledger_app_builder.py
```

Or, if the app has already been generated:

```python
from usekit import use

use.exec.pyp.base("examples.ledger_app.main")
```
