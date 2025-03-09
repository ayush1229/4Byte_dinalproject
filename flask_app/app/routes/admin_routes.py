# routes/admin_routes.py
from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_required, login_user, logout_user, current_user
from web3.exceptions import ContractLogicError
from datetime import datetime
from app.blockchain import w3, contract, account
from .. import mongo
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from app.decorators import admin_required
from app.user import User

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route("/create-session", methods=["GET", "POST"])
@login_required
@admin_required
def create_session():
    if request.method == "POST":
        try:
            start_time_str = request.form.get("start-time")
            end_time_str = request.form.get("end-time")
            candidate_names = request.form.getlist("candidate_name")

            fmt = "%Y-%m-%dT%H:%M"
            start_time = datetime.strptime(start_time_str, fmt)
            end_time = datetime.strptime(end_time_str, fmt)
            duration = int((end_time - start_time).total_seconds())
            
            if duration <= 0 or not candidate_names:
                flash("Invalid input parameters", "error")
                return redirect(url_for('admin.create_session'))
            
            session_name = f"Session from {start_time_str} to {end_time_str}"
            
            nonce = w3.eth.get_transaction_count(account.address)
            txn = contract.functions.createVotingSession(
                session_name, 
                candidate_names, 
                duration
            ).build_transaction({
                'chainId': 11155111,
                'gas': 500000,
                'gasPrice': w3.to_wei('10', 'gwei'),
                'nonce': nonce,
            })
            signed_txn = w3.eth.account.sign_transaction(txn, private_key=account.privateKey)
            tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

            session_data = {
                "name": session_name,
                "start_time": start_time,
                "end_time": end_time,
                "candidates": candidate_names,
                "created_by": ObjectId(current_user.id),
                "tx_hash": tx_hash.hex(),
                "created_at": datetime.utcnow()
            }
            mongo.db.sessions.insert_one(session_data)

            mongo.db.admin_logs.insert_one({
                "admin_id": ObjectId(current_user.id),
                "action": "create_session",
                "details": f"Created session: {session_name}",
                "timestamp": datetime.utcnow()
            })

            flash(f"Session creation initiated. Transaction hash: {tx_hash.hex()}", "success")
            return redirect(url_for('admin.dashboard'))

        except ContractLogicError as cle:
            flash(f"Contract logic error: {str(cle)}", "error")
            mongo.db.admin_logs.insert_one({
                "admin_id": ObjectId(current_user.id) if current_user.is_authenticated else None,
                "action": "create_session_error",
                "error": str(cle),
                "timestamp": datetime.utcnow()
            })
            return redirect(url_for('admin.create_session'))
    
        except Exception as e:
            flash(f"An error occurred: {str(e)}", "error")
            mongo.db.admin_logs.insert_one({
                "admin_id": ObjectId(current_user.id) if current_user.is_authenticated else None,
                "action": "create_session_error",
                "error": str(e),
                "timestamp": datetime.utcnow()
            })
            return redirect(url_for('admin.create_session'))

    return render_template("create-voting-session.html")

@admin_bp.route("/release-results", methods=["GET", "POST"])
@login_required
@admin_required
def release_results():
    if request.method == "POST":
        try:
            session_id = int(request.form.get("session_id"))
            
            nonce = w3.eth.get_transaction_count(account.address)
            txn = contract.functions.releaseResults(session_id).build_transaction({
                'chainId': 11155111,
                'gas': 200000,
                'gasPrice': w3.to_wei('10', 'gwei'),
                'nonce': nonce,
            })
            signed_txn = w3.eth.account.sign_transaction(txn, private_key=account.privateKey)
            tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

            mongo.db.election_results.insert_one({
                "session_id": session_id,
                "tx_hash": tx_hash.hex(),
                "released_by": ObjectId(current_user.id),
                "release_time": datetime.utcnow()
            })

            mongo.db.admin_logs.insert_one({
                "admin_id": ObjectId(current_user.id),
                "action": "release_results",
                "details": f"Released results for session {session_id}",
                "timestamp": datetime.utcnow()
            })

            flash(f"Results release initiated. Transaction hash: {tx_hash.hex()}", "success")
            return redirect(url_for('admin.dashboard'))

        except ContractLogicError as cle:
            flash(f"Contract logic error: {str(cle)}", "error")
            mongo.db.admin_logs.insert_one({
                "admin_id": ObjectId(current_user.id),
                "action": "release_results_error",
                "error": str(cle),
                "timestamp": datetime.utcnow()
            })
            return redirect(url_for('admin.release_results'))
    
        except Exception as e:
            flash(f"An error occurred: {str(e)}", "error")
            mongo.db.admin_logs.insert_one({
                "admin_id": ObjectId(current_user.id),
                "action": "release_results_error",
                "error": str(e),
                "timestamp": datetime.utcnow()
            })
            return redirect(url_for('admin.release_results'))

    return render_template("release_results.html")

@admin_bp.route("/view-results")
@login_required
@admin_required
def view_results():
    try:
        session_id = request.args.get("session_id", default=0, type=int)
        options, counts = contract.functions.getResults(session_id).call()
        results_data = list(zip(options, counts))
        return render_template("view_results.html", results=results_data)
    except ContractLogicError as cle:
        flash(f"Contract logic error: {str(cle)}", "error")
        return render_template("view_results.html", results=[])
    except Exception as e:
        flash(f"Error fetching results: {str(e)}", "error")
        return render_template("view_results.html", results=[])

@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            admin_id = request.form.get("adminId")
            admin_password = request.form.get("adminPassword")

            admin_user = mongo.db.users.find_one({
                "username": admin_id,
                "role": "admin"
            })

            if admin_user and check_password_hash(admin_user['password'], admin_password):
                user = User(
                    id=str(admin_user['_id']),
                    username=admin_user['username'],
                    role=admin_user['role']
                )
                login_user(user)

                mongo.db.admin_logs.insert_one({
                    "admin_id": admin_user['_id'],
                    "action": "login_success",
                    "timestamp": datetime.utcnow()
                })

                return redirect(url_for('admin.dashboard'))

            mongo.db.admin_logs.insert_one({
                "attempted_user": admin_id,
                "action": "login_failed",
                "timestamp": datetime.utcnow()
            })
            flash("Invalid admin credentials", "error")

        except Exception as e:
            mongo.db.admin_logs.insert_one({
                "action": "login_error",
                "error": str(e),
                "timestamp": datetime.utcnow()
            })
            flash("Login error occurred", "error")

    return render_template("admin.html")

@admin_bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    return render_template("admin-dashboard.html")

@admin_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for('admin.login'))

@admin_bp.route("/audit-logs")
@login_required
@admin_required
def audit_logs():
    logs = list(mongo.db.admin_logs.find().sort("timestamp", -1).limit(100))
    return render_template("audit_logs.html", logs=logs)

@admin_bp.route("/create-admin", methods=["GET", "POST"])
@login_required
@admin_required
def create_admin():
    if request.method == "POST":
        try:
            username = request.form.get("username")
            password = generate_password_hash(request.form.get("password"))

            mongo.db.users.insert_one({
                "username": username,
                "password": password,
                "role": "admin",
                "created_at": datetime.utcnow(),
                "created_by": ObjectId(current_user.id)
            })
            
            flash("Admin user created successfully", "success")
            return redirect(url_for('admin.dashboard'))

        except Exception as e:
            flash(f"Error creating admin: {str(e)}", "error")

    return render_template("create_admin.html")