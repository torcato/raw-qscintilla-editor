from setuptools import setup, find_packages

version = "0.9"
print("Using version for Python package:", version)

setup(
    name='raw-editor',
    url='https://www.raw-labs.com/',
    description='RAW query editor in PyQt',
    author='RAW Labs S.A.',
    author_email='support@raw-labs.com',
    version=version,
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=['raw_editor'],
    install_requires=[
        'rawapi',
        'PyQt5>=5.11.0',
        'QScintilla>=2.10.0'
    ],
    entry_points={
        'gui_scripts': [
            'raw-editor=raw_editor:main'
        ]
    }
)
