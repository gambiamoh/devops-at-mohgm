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
cd devops-at-mohgm/upkeep/lotcode_issues/automation
```

3. Create a python virtual environment and activate it:

```bash
python3 -m venv venv
source venv/bin/activate
```

4. install the required packages:

```bash
pip install -r requirements.txt
```

5. Run your desired script:

Example:

```bash
python fix_lotcode_issues.py
```
