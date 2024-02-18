# DevOps Tools and Docs - MoH Gambia

A set of python scripts to automate the fixing of lotcode issues in the eLMIS system caused by the Master Data upload.
<br>
<br>

# Pre-requisites

-   Python 3.6 or higher
-   pip

How to use the scripts

1. Clone the repository to your local machine:

```bash
git clone git@github.com:gambiamoh/devops-at-mohgm.git
```

2. Change directory to this folder:

```bash
cd devops-at-mohgm/upkeep/lotcode_issues
```

3. Create data and processed folders and add physicalInventories.json, orderables.json and orderables_tradeitems_lotcode.csv files to the data folder:

```bash
mkdir data processed
```

4. Create a python virtual environment and activate it:

```bash
python3 -m venv venv
source venv/bin/activate
```

5. install the required packages:

```bash
pip install -r requirements.txt
```

6. Run your desired script:

Example:

```bash
python fix_lotcode_issues.py
```

7. Find the processed files in the processed folder.
