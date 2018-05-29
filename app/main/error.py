from . import main

@main.app_errorhandler(404)
def page_not_found(e):
    return 'NONONOT FOUND', 404

@main.app_errorhandler(500)
def internal_server_error(e):
    return 'This is a very internal server error!', 500
