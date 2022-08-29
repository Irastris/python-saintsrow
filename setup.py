from setuptools import setup, find_packages

setup(
    name="python-saintsrow",
    description="An experimental CLI toolset designed expressly for \"Saints Row (2022)\"",
    version="0.1.0",
    author="Irastris",
    url="https://github.com/Irastris/python-saintsrow",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click",
        "lz4",
        "progressbar2",
    ],
    entry_points={
        "console_scripts": [
            "sr5tool = python_saintsrow.main:cli",
        ],
    },
)
