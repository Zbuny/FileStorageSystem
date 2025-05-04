from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField, StringField
from wtforms.validators import InputRequired
from werkzeug.utils import secure_filename

class UploadForm(FlaskForm):
    file = FileField('Upload File', validators=[InputRequired()])
    submit = SubmitField('Upload')

class UpdateFileForm(FlaskForm):
    new_filename = StringField('New Filename', validators=[InputRequired()])
    file = FileField('Upload New File')
    submit = SubmitField('Update File')
