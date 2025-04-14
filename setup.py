import os

from setuptools import find_packages, setup

# Read the requirements from the requirements.txt file
with open("requirements.txt", encoding="utf-8") as f:
    requirements = f.read().splitlines()

# Read the long description from README.md
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()


# Get the version from __init__.py
def get_version():
    with open(os.path.join("promoai", "__init__.py"), "r") as f:
        for line in f:
            if line.startswith("__version__"):
                _, version = line.split("=")
                return version.strip().replace("'", "").replace('"', "")
    raise RuntimeError("Unable to find __version__ string.")


version = get_version()

setup(
    name="promoai",
    version=version,
    description="ProMoAI: Process Modeling with Generative AI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Humam Kourani",
    author_email="humam.kourani@gmail.com",
    url="https://github.com/humam-kourani/ProMoAI",
    license="GPL-3.0",
    packages=find_packages(),
    install_requires=requirements,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    keywords="process modeling, business process management, generative AI",
    python_requires=">=3.9",
    # Include any data files (if any)
    # For example: package_data={'your_package': ['data/*.txt']},
    # Or: include_package_data=True  (to include everything in MANIFEST.in)
    # Entry points for command-line scripts (if any)
    # entry_points={
    #     'console_scripts': [
    #         'your_script_name = your_package.module:main_function',
    #     ],
    # },
)
