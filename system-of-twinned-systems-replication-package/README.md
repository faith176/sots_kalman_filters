# Replication package

### for the article _Systems of Twinned Systems: A Systematic Literature Review_.

[![License](https://img.shields.io/badge/license-GPL--3.0-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

## About
Systems of Twinned Systems (SoTS) bring together Digital Twins (DTs) and Systems of Systems (SoS) by combining multiple physical and digital systems in coordinated ways. This includes both networks of DTs working together and single DTs managing multiple systems. As real-world systems become more complex and connected, understanding how to design and manage SoTS is increasingly important. To support this, we systematically review the academic literature on SoTS, clarify key concepts, and identify common patterns, challenges, and future directions for researchers and practitioners.

## Contents

- `/data` - Data extraction sheet of the included primary studies (with fully extracted data)
- `/scripts` - Analysis scripts for the automated analysis of data
- `/output` - Results of the analyses as used in the article

## How to use
To avoid dependency conflicts and ensure a clean environment, it is recommended to run this package inside a Python virtual environment

### Set up virtual environment
- Create virtual environment: `python -m venv venv`
- Activate environment: `venv\Scripts\activate`

### Install requirements
- Install requirements by executing `pip install -r requirements.txt` from the root folder.

### Run analysis
- For publication trends: execute `python .\scripts\publication_trends.py` from the root folder.
- For the quality report: execute `python .\scripts\quality.py` from the root folder.
- For the result figures: execute `python .\scripts\figure_generation.py` from the root folder.
- For the result tables: execute `python .\scripts\table_generation.py` from the root folder.
