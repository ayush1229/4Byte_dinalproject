# routes/voter_routes.py
from flask import Blueprint, request, render_template, redirect, url_for, flash
from web3.exceptions import ContractLogicError, TransactionNotFound
from app.forms import VoterForm
from flask import current_app
from bson import ObjectId
from datetime import datetime


voter_bp = Blueprint('voter', __name__)

def get_mongo():
    return current_app.extensions['pymongo'].mongo

@voter_bp.route("/vote", methods=["GET", "POST"])
def vote():
    from ..blockchain import w3, contract, account  # Move import here to avoid circular dependency
    
    form = VoterForm()
    mongo = get_mongo()
    VOTER_IDS_COLLECTION = mongo.db.voter_ids
    ERROR_LOGS_COLLECTION = mongo.db.error_logs
    VOTER_LOGS_COLLECTION = mongo.db.voter_logs
    
    if form.validate_on_submit():
        voter_id = form.voter_id.data.strip()
        session_id = form.session_id.data
        option = form.option.data.strip()
        
        try:
            # 1. Validate voting session status
            is_active = contract.functions.isSessionActive(session_id).call()
            if not is_active:
                flash("Voting session is not active", "error")
                return redirect(url_for('voter.vote'))

            # 2. Check voter ID validity
            voter_record = VOTER_IDS_COLLECTION.find_one({"voter_id": voter_id, "used": False})
            if not voter_record:
                flash("Invalid or already used voter ID", "error")
                return render_template("voter.html", form=form)

            # 3. Prepare blockchain transaction
            nonce = w3.eth.get_transaction_count(account.address)
            txn = contract.functions.vote(
                int(session_id), 
                option
            ).build_transaction({
                'chainId': 11155111,
                'gas': 300000,
                'gasPrice': w3.to_wei('20', 'gwei'),
                'nonce': nonce,
            })

            # 4. Sign and send transaction
            signed_txn = w3.eth.account.sign_transaction(txn, private_key=account.privateKey)
            tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # 5. Wait for transaction confirmation
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120, poll_latency=0.1)
            
            if receipt.status != 1:
                raise ContractLogicError("Transaction failed in blockchain")

            # 6. Update MongoDB after confirmation
            VOTER_IDS_COLLECTION.update_one(
                {"_id": ObjectId(voter_record['_id'])},
                {"$set": {
                    "used": True,
                    "tx_hash": tx_hash.hex(),
                    "used_at": datetime.utcnow()
                }}
            )

            flash("Vote recorded successfully!", "success")
            return redirect(url_for('voter.results', session_id=session_id))

        except ContractLogicError as cle:
            flash(f"Voting error: {str(cle)}", "error")
            VOTER_LOGS_COLLECTION.insert_one({
                "voter_id": voter_id,
                "error": str(cle),
                "timestamp": datetime.utcnow()
            })
            
        except TransactionNotFound:
            flash("Transaction confirmation timed out", "error")
            
        except Exception as e:
            flash("Failed to process vote - please try again", "error")
            ERROR_LOGS_COLLECTION.insert_one({
                "voter_id": voter_id,
                "error": str(e),
                "timestamp": datetime.utcnow()
            })

    return render_template("voter.html", form=form)

@voter_bp.route("/results")
def results():
    from app.blockchain import contract  # Move import here
    
    try:
        session_id = int(request.args.get("session_id", 0))
        options, counts = contract.functions.getResults(session_id).call()
        results_data = list(zip(options, counts))
        return render_template("results.html", results=results_data, session_id=session_id)
    
    except ContractLogicError as cle:
        flash(f"Contract error: {str(cle)}", "error")
        return render_template("results.html", results=[])
    
    except Exception as e:
        flash(f"Error fetching results: {str(e)}", "error")
        return render_template("results.html", results=[])

@voter_bp.route("/home")
def home():
    return render_template("voter.html")

@voter_bp.route("/about")
def about():
    return render_template("about.html")

@voter_bp.route("/candidates")
def candidates():
    return render_template("candidates.html")

@voter_bp.route("/importance")
def importance():
    return render_template("importance.html")

@voter_bp.route('/')
def index():
    return render_template("index.html")