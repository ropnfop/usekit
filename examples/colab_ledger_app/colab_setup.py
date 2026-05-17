"""
Mobile Colab setup for USEKIT.

Run these lines in Google Colab.

Notebook cell version:

    from google.colab import drive
    drive.mount("/content/drive")

    !pip install usekit

    from usekit import use
    use.colab()
"""

from google.colab import drive
from usekit import use

drive.mount("/content/drive")
use.colab()
