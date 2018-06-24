Setup virtual environment
Goto folder of project
python -m venv venv --prompt <Project name>
source venv/bin/activate
pip install -e . # req setup.py editable mode so i can edit code wihile still beeing able to import it in tests
pycharm .