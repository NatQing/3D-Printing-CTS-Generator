Install Procedure:
1. download this whole folder
2. download IDE of choice (eg. VSCODE or sth)
3. open this folder in IDE
4. open up a terminal window in IDE
5. check if python 3.9.12 is installed by running ```python3 --version```
6. if displayed version does not match 3.9.12, download python 3.9.12 from ```https://www.python.org/downloads/release/python-3912/```
7. check if pip3 is installed using ```pip3 --version```
8. if not installed, install pip3 with ```sudo apt install python3-pip```
9. close and reopen terminal window after installation process
10. check that you are in the correct folder with```ls```, you should find the requirements.txt file listed
11. if not, find the path to ```requirements.txt```, copy it
12. then do ```pip3 install -r /path/to/requirements.txt```, replace ```/path/to/requirements.txt``` with your copied path
13. else if you are in the correct folder do ```pip3 install -r requirements.txt```
14. try to run the ```CTS_determinant.py``` file
15. IF ANY IMPORTS ARE MISSING, CONSULT GOOGLE WITH "HOW TO INSTALL ```INSERT MISSING IMPORT```"
