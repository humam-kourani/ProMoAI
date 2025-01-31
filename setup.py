import os
from setuptools import setup, find_packages

# Read the requirements from the requirements.txt file
with open('requirements.txt', encoding='utf-8') as f:
    requirements = f.read().splitlines()

# Read the long description from README.md
with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

# Get the version from _init_.py
def get_version():
    with open(os.path.join('promoai', '__init__.py'), 'r') as f:
        for line in f:
            if line.startswith('__version__'):
                _, version = line.split("=")
                return version.strip().replace("'", "").replace('"', '')
    raise RuntimeError("Unable to find __version__ string.")

version = get_version()

setup(
    name='promoai',  # Choose a unique and descriptive name
    version=version,  # Use dynamic versioning
    description='A brief description of your project',  # Short description
    long_description=long_description,  # Long description from README
    long_description_content_type='text/markdown',  # Specify Markdown format
    author='Your Name',  # Your name or organization name
    author_email='your.email@example.com',  # Your email address
    url='https://github.com/yourusername/promoai',  # Link to your project's repository
    license='MIT',  # Choose an appropriate license (e.g., MIT, Apache 2.0)
    packages=find_packages(),  # Automatically find and include all packages
    install_requires=requirements,  # Dependencies from requirements.txt
    classifiers=[  # Trove classifiers for categorization
        'Development Status :: 3 - Alpha',  # Or appropriate status
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',  # Match your chosen license
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        # Add more classifiers as needed (e.g., operating system, topic)
    ],
    keywords='keyword1, keyword2, keyword3',  # Relevant keywords for searchability
    python_requires='>=3.7',  # Specify the minimum Python version
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
