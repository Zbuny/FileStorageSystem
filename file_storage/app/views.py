import os
from flask import render_template, redirect, url_for, flash, request, session, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from . import db
from .models_form import User, File, RegisterForm, LoginForm, UploadForm
from config import Config
from datetime import timedelta
from flask import current_app as app

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def generate_unique_filename(filename):
    base_name, ext = os.path.splitext(filename)
    counter = 1
    while File.query.filter_by(filename=filename).first() is not None:
        filename = f"{base_name} ({counter}){ext}"
        counter += 1
    return filename

@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=15)

@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash("Username already exists")
            return redirect(url_for('register'))
        hashed = generate_password_hash(form.password.data)
        user = User(username=form.username.data, password=hashed)
        db.session.add(user)
        db.session.commit()
        flash("Registered successfully")
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash("Invalid credentials")
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    form = UploadForm()
    if form.validate_on_submit() and 'file' in request.files:
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = generate_unique_filename(secure_filename(file.filename))
            path = os.path.join(Config.UPLOAD_FOLDER, filename)
            file.save(path)
            f = File(filename=filename, size=os.path.getsize(path), user_id=current_user.id)
            db.session.add(f)
            db.session.commit()
            flash("File uploaded")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid file type")
    files = File.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', form=form, files=files)

@app.route('/update/<int:file_id>', methods=['GET', 'POST'])
@login_required
def update_file(file_id):
    file = File.query.get_or_404(file_id)
    if file.user_id != current_user.id:
        flash("You don't have permission to edit this file.")
        return redirect(url_for('dashboard'))

    form = UploadForm()
    if form.validate_on_submit():
        new_filename = request.form.get('new_filename')
        if new_filename:
            new_filename = secure_filename(new_filename)
            base, ext = os.path.splitext(new_filename)
            new_path = os.path.join(Config.UPLOAD_FOLDER, new_filename)
            counter = 1
            while os.path.exists(new_path) and new_filename != file.filename:
                new_filename = f"{base} ({counter}){ext}"
                new_path = os.path.join(Config.UPLOAD_FOLDER, new_filename)
                counter += 1
            old_path = os.path.join(Config.UPLOAD_FOLDER, file.filename)
            os.rename(old_path, new_path)
            file.filename = new_filename
            file.size = os.path.getsize(new_path)
            db.session.commit()
            flash("File name updated successfully!")

        if 'file' in request.files:
            new_file = request.files['file']
            if new_file and allowed_file(new_file.filename):
                filename = generate_unique_filename(secure_filename(new_file.filename))
                path = os.path.join(Config.UPLOAD_FOLDER, filename)
                new_file.save(path)
                file.filename = filename
                file.size = os.path.getsize(path)
                db.session.commit()
                flash("File updated successfully!")

        return redirect(url_for('dashboard'))

    return render_template('update_file.html', form=form, file=file)


@app.route('/delete/<int:file_id>', methods=['POST'])
@login_required
def delete_file(file_id):
    file = File.query.get_or_404(file_id)
    if file.owner != current_user:
        flash("Access denied")
        return redirect(url_for('dashboard'))
    path = os.path.join(Config.UPLOAD_FOLDER, file.filename)
    if os.path.exists(path):
        os.remove(path)
    db.session.delete(file)
    db.session.commit()
    flash("File deleted")
    return redirect(url_for('dashboard'))

@app.route('/files')
@login_required
def files():
    files = File.query.filter_by(user_id=current_user.id).all()
    return render_template('files.html', files=files)

@app.route('/download/<int:file_id>')
@login_required
def download_file(file_id):
    file = File.query.get_or_404(file_id)
    if file.user_id != current_user.id:
        flash("You do not have permission to download this file.")
        return redirect(url_for('dashboard'))

    return send_from_directory(Config.UPLOAD_FOLDER, file.filename, as_attachment=True)
