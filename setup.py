from setuptools import setup


setup(
    name="bump",
    version="1.3.2",
    description="Bumps package version numbers",
    long_description=open("README.rst").read(),
    license="MIT",
    url="https://github.com/di/bump",
    author="Mark Steve Samson",
    author_email="hello@marksteve.com",
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    keywords="bump increment package version",
    zip_safe=False,
    py_modules=["bump"],
    install_requires=[
        "click>=6,<9",
        "first",
        "packaging>=17.1",
        "toml",
    ],
    extras_require={
        "dev": [
            "pytest",
            "black",
            "build",
            "twine",
        ]
    },
    entry_points={"console_scripts": ["bump = bump:main"]},
)
