<div align="center">
  <h1>QtSnake</h1>
  <h4>Simple educational python Snake game created with PySide6 and Qt framework</h4>
  <img src="https://github.com/gudarzi/QtSnake/assets/30085894/c4dbea2a-aebc-4ba8-896c-ab20c06c0799" alt="Screen Shot of QtSnake Game">
</div>


## Table of Contents
1. [How to Run](#how-to-run)
2. [How to Build to EXE](#how-to-build-to-exe)
3. [Issues](#issues)
4. [How to Contribute](#how-to-contribute)
5. [Disclaimer](#disclaimer)


## How to Run
To run the project:
1. Make sure you have Python 3.x installed.
2. Navigate to the project folder and install project requirements using pip:
```
pip install -r requirements.txt
```
3. Run the project:
```
python main.py
```
4. Use keyboard arrows to play.


## How to Build to EXE
Use this command to compile the game into an `exe` executable:
```
pyinstaller --noconfirm --onefile --windowed --add-data "main.ui;."  "main.py"
```


## Issues
If you encounter any issues while running or building the project, please check out the [Issues](https://github.com/gudarzi/QtSnake/issues) section. There, you might find solutions to common problems or issues that other contributors are working on.

To submit a new issue, click on the "New issue" button and provide a detailed description of the problem. Include any relevant error messages and steps to reproduce the issue. This will help us address the problem as quickly and effectively as possible.


## How to Contribute
If you're interested in contributing to QtSnake, check out [Issues](https://github.com/gudarzi/QtSnake/issues) page for open issues. Leave a comment to claim an issue and submit a pull request with your proposed changes. Thank you for your interest in this project.


## Disclaimer
Please note that this project is intended for educational purposes and might not be suitable for production environments. The project is provided "as is", without warranty of any kind. In no event shall the authors or copyright holders be liable for any claim, damages or other liability arising from the use of this project.

