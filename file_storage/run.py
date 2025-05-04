from app import create_app
from datetime import datetime


app = create_app()
@app.context_processor
def inject_now():
    return {'current_year': datetime.now().year}

if __name__ == '__main__':
    app.run(debug=True)
