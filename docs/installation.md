# Installation and Setup

There are several strategies for installation. First, be sure to confirm that your system meets the requirements for installation.

## Requirements

- MacOS or Linux operating system
- `python3.9` or higher
- `cmake 3.2.0` or higher
- `gcc` of any version (In our analysis, `gcc 9.2.0` was used)

## Installation via Cloning

- Clone the cm_pipeline repository
- Activate the venv which has the necessary packages
- Run `pip install -r requirements.txt && pip install .`
- Make sure everything installed properly by running `cd tests && pytest`

## Installation via pip install

Simply run `pip install git+https://github.com/illinois-or-research-analytics/cm_pipeline`. **This will install CM++, but to use pipeline functionality, please setup via cloning.**
