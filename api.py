from flask import Blueprint, request, jsonify
from models import db, Note
from auth_firebase import requires_firebase_auth
from flask_cors import cross_origin

bp = Blueprint("api", __name__, url_prefix="/api")

def _iso(dt):
    return (dt.isoformat() if dt else None)

@bp.route("/notes", methods=["GET"])
@requires_firebase_auth
@cross_origin()
def list_notes():
    user = getattr(__import__('flask')._request_ctx_stack.top, "current_user", None)
    uid = user.get("uid")
    notes = Note.query.filter_by(owner_id=uid).order_by(Note.updated_at.desc()).all()
    results = [
        {
            "id": n.id,
            "title": n.title,
            "content": n.content or "",
            "created_at": _iso(n.created_at),
            "updated_at": _iso(n.updated_at),
        }
        for n in notes
    ]
    return jsonify(results), 200

@bp.route("/notes", methods=["POST"])
@requires_firebase_auth
@cross_origin()
def create_note_api():
    user = getattr(__import__('flask')._request_ctx_stack.top, "current_user", None)
    uid = user.get("uid")
    data = request.get_json() or {}
    title = (data.get("title") or "").strip()
    content = data.get("content") or ""
    if not title:
        return jsonify({"message": "Title is required"}), 400
    note = Note(owner_id=uid, title=title, content=content)
    db.session.add(note)
    db.session.commit()
    return jsonify({"id": note.id}), 201

@bp.route("/notes/<int:note_id>", methods=["GET"])
@requires_firebase_auth
@cross_origin()
def get_note_api(note_id):
    user = getattr(__import__('flask')._request_ctx_stack.top, "current_user", None)
    uid = user.get("uid")
    note = Note.query.get_or_404(note_id)
    if note.owner_id != uid:
        return jsonify({"message": "Forbidden"}), 403
    return jsonify({"id": note.id, "title": note.title, "content": note.content}), 200

@bp.route("/notes/<int:note_id>", methods=["PUT", "PATCH"])
@requires_firebase_auth
@cross_origin()
def update_note_api(note_id):
    user = getattr(__import__('flask')._request_ctx_stack.top, "current_user", None)
    uid = user.get("uid")
    note = Note.query.get_or_404(note_id)
    if note.owner_id != uid:
        return jsonify({"message": "Forbidden"}), 403
    data = request.get_json() or {}
    title = (data.get("title") or "").strip()
    content = data.get("content") or ""
    if not title:
        return jsonify({"message": "Title is required"}), 400
    note.title = title
    note.content = content
    db.session.commit()
    return jsonify({"message": "Updated"}), 200

@bp.route("/notes/<int:note_id>", methods=["DELETE"])
@requires_firebase_auth
@cross_origin()
def delete_note_api(note_id):
    user = getattr(__import__('flask')._request_ctx_stack.top, "current_user", None)
    uid = user.get("uid")
    note = Note.query.get_or_404(note_id)
    if note.owner_id != uid:
        return jsonify({"message": "Forbidden"}), 403
    db.session.delete(note)
    db.session.commit()
    return jsonify({"message": "Deleted"}), 200