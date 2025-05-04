import os
import random
import string
from flask import render_template, redirect, url_for, flash, request, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from . import files_bp
from ..models.models_form import User, File, RegisterForm, LoginForm, UploadForm
from config import Config
from app import db

def generate_unique_filename(filename):
    base, ext = os.path.splitext(filename)
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    unique_filename = f"{base}_{random_suffix}{ext}"
    return unique_filename

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


@files_bp.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    form = UploadForm()
    search_query = request.args.get('search', '').strip()

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
            return redirect(url_for('files.dashboard'))
        else:
            flash("Invalid file type")

    files = File.query.filter_by(user_id=current_user.id).all() if not search_query else \
        File.query.filter(File.user_id == current_user.id, File.filename.ilike(f"%{search_query}%")).all()

    return render_template('dashboard.html', form=form, files=files, search_query=search_query)


@files_bp.route('/update/<int:file_id>', methods=['GET', 'POST'])
@login_required
def update_file(file_id):
    file = File.query.get_or_404(file_id)
    if file.user_id != current_user.id:
        flash("You don't have permission to edit this file.")
        return redirect(url_for('files.dashboard'))

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

        return redirect(url_for('files.dashboard'))

    return render_template('update_file.html', form=form, file=file)


@files_bp.route('/delete/<int:file_id>', methods=['POST'])
@login_required
def delete_file(file_id):
    file = File.query.get_or_404(file_id)
    if file.owner != current_user:
        flash("Access denied")
        return redirect(url_for('files.dashboard'))

    path = os.path.join(Config.UPLOAD_FOLDER, file.filename)
    if os.path.exists(path):
        os.remove(path)
    db.session.delete(file)
    db.session.commit()
    flash("File deleted")
    return redirect(url_for('files.dashboard'))


@files_bp.route('/files')
@login_required
def files():
    files = File.query.filter_by(user_id=current_user.id).all()
    return render_template('files.html', files=files)


@files_bp.route('/download/<int:file_id>')
@login_required
def download_file(file_id):
    file = File.query.get_or_404(file_id)
    if file.user_id != current_user.id:
        flash("You do not have permission to download this file.")
        return redirect(url_for('files.dashboard'))

    return send_from_directory(Config.UPLOAD_FOLDER, file.filename, as_attachment=True)


@files_bp.route('/view/<int:file_id>')
@login_required
def view_file(file_id):
    file = File.query.get_or_404(file_id)
    if file.user_id != current_user.id:
        flash("You do not have permission to view this file.")
        return redirect(url_for('files.dashboard'))

    try:
        return send_from_directory(Config.UPLOAD_FOLDER, file.filename)
    except FileNotFoundError:
        flash("File not found.")
        return redirect(url_for('files.dashboard'))
