from . import main

@main.route('/')
def index():
    return 'This is the start page!!!'
