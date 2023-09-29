from setuptools import setup, find_packages

setup(
    name="hm01",
    version="3.4.3",
    author="Vikram Ramavarapu, Fabio Ayres, Vidya Kamath Pailodi, Minhyuk Park",
    author_email="vikramr2@illinois.edu",
    description="Modular pipeline for testing and using an improved version of CM for generating well-connected clusters.",
    long_description="Modular pipeline for testing and using an improved version of CM for generating well-connected clusters.",
    long_description_content_type="text/markdown",
    url="https://github.com/illinois-or-research-analytics/cm_pipeline",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GPL v3.0 License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.9",
)
