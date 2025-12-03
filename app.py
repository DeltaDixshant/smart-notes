from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Note
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET", "dev-secret-12345")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///smartnotes.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SESSION_PERMANENT"] = True
app.config["REMEMBER_COOKIE_DURATION"] = 86400

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()
    print("✅ Database created!")

# ========== AUTHENTICATION ==========

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        
        if not email or not password:
            flash("Email and password are required.", "danger")
            return render_template("register.html")
        
        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")
        
        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return render_template("register.html")
        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered. Please login.", "danger")
            return redirect(url_for('login'))
        
        user = User(email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        print(f"✅ New user registered: {email} (ID: {user.id})")
        flash(f"Account created! Logging you in...", "success")
        
        login_user(user, remember=True)
        print(f"✅ User {email} logged in (session established)")
        
        return redirect(url_for('index'))
    
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        
        if not email or not password:
            flash("Email and password are required.", "danger")
            return render_template("login.html")
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user, remember=True)
            print(f"✅ {email} logged in (ID: {user.id})")
            flash(f"Welcome back, {email}!", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid email or password.", "danger")
    
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    print(f"✅ {current_user.email} logged out")
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

# ========== NOTES ==========

def check_note_ownership(note):
    """FIX: Proper ownership check with type conversion"""
    if not note:
        return False
    
    # Convert both to int to ensure comparison works
    note_owner = int(note.owner_id)
    user_id = int(current_user.id)
    
    return note_owner == user_id

@app.route("/")
@login_required
def index():
    """Home page"""
    notes = Note.query.filter_by(owner_id=current_user.id).order_by(Note.updated_at.desc()).all()
    print(f"✅ {current_user.email} (ID: {current_user.id}) - Showing {len(notes)} notes")
    return render_template("index.html", notes=notes)

@app.route("/notes/new", methods=["GET", "POST"])
@login_required
def create_note():
    """Create note"""
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        
        if not title:
            flash("Title is required.", "danger")
            return render_template("create.html")
        
        note = Note(owner_id=current_user.id, title=title, content=content)
        db.session.add(note)
        db.session.commit()
        
        print(f"✅ Note created - ID: {note.id}, Owner ID: {current_user.id}, User: {current_user.email}")
        flash("Note created successfully!", "success")
        return redirect(url_for("index"))
    
    return render_template("create.html")

@app.route("/notes/<int:note_id>")
@login_required
def view_note(note_id):
    """View note"""
    note = Note.query.get(note_id)
    
    if not note:
        print(f"❌ Note {note_id} not found")
        flash("Note not found.", "danger")
        return redirect(url_for("index"))
    
    # FIX: Use proper ownership check
    if not check_note_ownership(note):
        print(f"❌ Access denied: {current_user.email} (ID: {current_user.id}) trying to view note {note_id}")
        flash("Access denied.", "danger")
        return redirect(url_for("index"))
    
    print(f"✅ {current_user.email} viewing note {note_id}")
    return render_template("view.html", note=note)

@app.route("/notes/<int:note_id>/edit", methods=["GET", "POST"])
@login_required
def edit_note(note_id):
    """Edit note"""
    note = Note.query.get(note_id)
    
    if not note:
        print(f"❌ Note {note_id} not found")
        flash("Note not found.", "danger")
        return redirect(url_for("index"))
    
    # FIX: Use proper ownership check
    if not check_note_ownership(note):
        print(f"❌ Access denied: {current_user.email} (ID: {current_user.id}) trying to edit note {note_id}")
        flash("Access denied.", "danger")
        return redirect(url_for("index"))
    
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        
        if not title:
            flash("Title is required.", "danger")
            return render_template("edit.html", note=note)
        
        note.title = title
        note.content = content
        db.session.commit()
        
        print(f"✅ {current_user.email} updated note {note_id}")
        flash("Note updated successfully!", "success")
        return redirect(url_for("view_note", note_id=note.id))
    
    return render_template("edit.html", note=note)

@app.route("/notes/<int:note_id>/delete", methods=["POST"])
@login_required
def delete_note(note_id):
    """Delete note"""
    note = Note.query.get(note_id)
    
    if not note:
        print(f"❌ Note {note_id} not found")
        flash("Note not found.", "danger")
        return redirect(url_for("index"))
    
    # FIX: Use proper ownership check
    if not check_note_ownership(note):
        print(f"❌ Access denied: {current_user.email} (ID: {current_user.id}) trying to delete note {note_id}")
        flash("Access denied.", "danger")
        return redirect(url_for("index"))
    
    note_title = note.title
    db.session.delete(note)
    db.session.commit()
    
    print(f"✅ {current_user.email} deleted note {note_id} ({note_title})")
    flash("Note deleted successfully!", "warning")
    return redirect(url_for("index"))

if __name__ == "__main__":
    print("🚀 Smart Notes - Flask-Login")
    app.run(host="0.0.0.0", port=8080, debug=True)