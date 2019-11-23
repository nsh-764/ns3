import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ns3",
    version="0.1.0",
    author="Nikhil S Hubballi",
    author_email="nikhil.hubballi@gmail.com",
    description="Nested S3 - Display the objects on S3 bucket path in a tree-like diagram",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nsh-764/ns3",
    packages = ['ns3'],
    install_requires= ['setuptools', 'awscli'],
    entry_points = {
        'console_scripts': ['ns3=ns3.main:main'],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: GNU General Public License v3.0",
        "Operating System :: OS Independent",
    ],
)
