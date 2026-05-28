from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from database import db
from models.user_model import User

auth_bp = Blueprint("auth", __name__)


# --------------------------------
# SIGNUP
# --------------------------------
@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()

    name     = data.get("name")
    email    = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({"error": "Missing fields"}), 400

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"error": "Email already registered"}), 400

    user = User(name=name, email=email)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    # Return a short-lived token so the frontend can immediately call /kyc/submit
    # without asking the user to log in first.
    token = create_access_token(identity=str(user.id))

    return jsonify({
        "message": "Account created successfully. Please complete KYC to continue.",
        "token": token,
        "user": {
            "id":         user.id,
            "name":       user.name,
            "email":      user.email,
            "kyc_status": user.kyc_status,
        }
    }), 201


# --------------------------------
# LOGIN  — blocked until KYC done
# --------------------------------
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    email    = data.get("email")
    password = data.get("password")

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401

    # Block login until KYC is approved
    if user.kyc_status != "approved":
        return jsonify({
            "error": "KYC verification required before logging in.",
            "kyc_status": user.kyc_status,
            "requires_kyc": True
        }), 403

    token = create_access_token(identity=str(user.id))

    return jsonify({
        "token": token,
        "user": {
            "id":         user.id,
            "name":       user.name,
            "email":      user.email,
            "kyc_status": user.kyc_status,
        }
    })


# --------------------------------
# PROFILE  (protected)
# --------------------------------
@auth_bp.route("/profile", methods=["GET"])
@jwt_required()
def profile():
    user_id = int(get_jwt_identity())
    user    = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "id":         user.id,
        "name":       user.name,
        "email":      user.email,
        "kyc_status": user.kyc_status,
    })


# --------------------------------
# KYC SUBMIT  — requires signup token
# --------------------------------
@auth_bp.route("/kyc/submit", methods=["POST"])
@jwt_required()
def kyc_submit():
    """
    Protected: caller must supply the JWT returned by /signup (or a previous /login
    if they somehow have one).  This ensures a registered user always exists before
    KYC is processed — fixing the 'User not found' bug that occurred when the
    frontend hit this endpoint without a valid token.
    """
    user_id = int(get_jwt_identity())
    user    = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found. Please register first."}), 404

    if user.kyc_status == "approved":
        return jsonify({"message": "KYC already approved", "kyc_status": "approved"})

    # In production: validate PAN / Aadhaar docs here.
    # Mock: approve immediately.
    user.kyc_status = "approved"
    db.session.commit()

    return jsonify({
        "message":    "KYC submitted and approved successfully.",
        "kyc_status": "approved",
    })


# --------------------------------
# KYC STATUS
# --------------------------------
@auth_bp.route("/kyc/status", methods=["GET"])
@jwt_required()
def kyc_status():
    user_id = int(get_jwt_identity())
    user    = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({"kyc_status": user.kyc_status})
