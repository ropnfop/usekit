from setuptools import setup, find_packages
from pathlib import Path

HERE = Path(__file__).parent

def read_readme() -> str:
    """
    Read README.md with fallback for TestPyPI upload.
    Prevents upload failures/warnings when README is missing.
    """
    readme = HERE / "README.md"
    if readme.exists():
        return readme.read_text(encoding="utf-8")
    # Fallback description for TestPyPI
    return "# usekit\n\nMinimal input, auto path toolkit (mobile-first, Colab+Drive)\n"

setup(
    name="usekit",
    version="0.2.0",
    author="ropnfop",
    author_email="withropnfop@gmail.com",
    description="Minimal input, auto path toolkit (mobile-first, Colab+Drive)",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/ropnfop/usekit",

    # Key: Exclude unnecessary folders from distribution
    # (tests, docs, examples not needed in wheel)
    packages=find_packages(exclude=("tests*", "docs*", "examples*")),
    include_package_data=True,

    # Key: Only include essential files in wheel
    # These files MUST be present in the distribution
    package_data={
        "usekit": [
            ".env.example",
            "sys/sys_yaml/sys_const.yaml",
        ],
    },

    python_requires=">=3.8",

    # Zero dependencies: loader_env.py auto-installs when needed
    # This completely eliminates pip dependency conflicts
    install_requires=[
        "PyYAML>=5.1",
        "python-dotenv>=0.10.0",
    ],

    # Optional dependencies for users who want pre-installation
    extras_require={
        "full": [
            "PyYAML>=5.1",
            "python-dotenv>=0.10.0",
        ],
        "dev": [
            "PyYAML>=5.1",
            "python-dotenv>=0.10.0",
            "pytest>=7.0",
            "black>=22.0",
            "flake8>=4.0",
        ],
    },

    # Key: Prevent file access issues when installed as zip
    # Especially important for mobile/Termux environments
    zip_safe=False,

    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: Console",
    ],
)
