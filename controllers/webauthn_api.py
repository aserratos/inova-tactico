import os
import json
from flask import Blueprint, request, jsonify, session
from flask_login import login_user, current_user, login_required
from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
)
from webauthn.helpers.structs import (
    RegistrationCredential,
    AuthenticationCredential,
    AuthenticatorSelectionCriteria,
    UserVerificationRequirement,
    AuthenticatorAttachment,
)
from webauthn.helpers.exceptions import InvalidRegistrationResponse, InvalidAuthenticationResponse
from webauthn.helpers import bytes_to_base64url, base64url_to_bytes, generate_user_handle

from models import db, User, WebAuthnCredential

webauthn_bp = Blueprint('webauthn_api', __name__, url_prefix='/api/webauthn')

RP_ID = os.environ.get('RP_ID', 'inova-tactico.vercel.app') # Or localhost when testing
RP_NAME = 'Inova Táctico'
ORIGIN = os.environ.get('FRONTEND_URL', 'https://inova-tactico.vercel.app')

# REGISTRATION

@webauthn_bp.route('/register/generate-options', methods=['POST'])
@login_required
def generate_registration():
    if not current_user.webauthn_id:
        current_user.webauthn_id = bytes_to_base64url(generate_user_handle())
        db.session.commit()

    existing_credentials = WebAuthnCredential.query.filter_by(user_id=current_user.id).all()
    exclude_credentials = [
        {"id": base64url_to_bytes(c.credential_id), "type": "public-key"}
        for c in existing_credentials
    ]

    options = generate_registration_options(
        rp_id=RP_ID,
        rp_name=RP_NAME,
        user_id=base64url_to_bytes(current_user.webauthn_id),
        user_name=current_user.email,
        user_display_name=current_user.nombre_completo or current_user.email,
        exclude_credentials=exclude_credentials,
        authenticator_selection=AuthenticatorSelectionCriteria(
            user_verification=UserVerificationRequirement.PREFERRED
        ),
    )

    # Convert to dict and store challenge in session
    options_dict = json.loads(options.json())
    session['registration_challenge'] = options_dict['challenge']

    return jsonify(options_dict)


@webauthn_bp.route('/register/verify', methods=['POST'])
@login_required
def verify_registration():
    data = request.json
    challenge = session.get('registration_challenge')
    
    if not challenge:
        return jsonify({'error': 'No active registration challenge'}), 400

    try:
        verification = verify_registration_response(
            credential=data,
            expected_challenge=base64url_to_bytes(challenge),
            expected_origin=ORIGIN,
            expected_rp_id=RP_ID,
            require_user_verification=False
        )
    except InvalidRegistrationResponse as e:
        return jsonify({'error': f'Registration failed: {e}'}), 400

    # Save the credential
    new_cred = WebAuthnCredential(
        user_id=current_user.id,
        credential_id=bytes_to_base64url(verification.credential_id),
        public_key=bytes_to_base64url(verification.credential_public_key),
        sign_count=verification.sign_count
    )
    db.session.add(new_cred)
    db.session.commit()

    del session['registration_challenge']
    return jsonify({'status': 'ok', 'message': 'Device registered successfully'})


# AUTHENTICATION (LOGIN)

@webauthn_bp.route('/login/generate-options', methods=['POST'])
def generate_auth():
    # If email provided, fetch their credentials. Otherwise, let authenticator decide.
    data = request.json or {}
    email = data.get('email')
    
    allow_credentials = []
    if email:
        user = User.query.filter_by(email=email).first()
        if user:
            creds = WebAuthnCredential.query.filter_by(user_id=user.id).all()
            allow_credentials = [
                {"id": base64url_to_bytes(c.credential_id), "type": "public-key"}
                for c in creds
            ]

    options = generate_authentication_options(
        rp_id=RP_ID,
        allow_credentials=allow_credentials,
        user_verification=UserVerificationRequirement.PREFERRED,
    )

    options_dict = json.loads(options.json())
    session['authentication_challenge'] = options_dict['challenge']

    return jsonify(options_dict)


@webauthn_bp.route('/login/verify', methods=['POST'])
def verify_auth():
    data = request.json
    challenge = session.get('authentication_challenge')

    if not challenge:
        return jsonify({'error': 'No active authentication challenge'}), 400

    credential_id = data.get('id')
    if not credential_id:
        return jsonify({'error': 'No credential ID provided'}), 400

    cred = WebAuthnCredential.query.filter_by(credential_id=credential_id).first()
    if not cred:
        return jsonify({'error': 'Credential not found in database'}), 404

    try:
        verification = verify_authentication_response(
            credential=data,
            expected_challenge=base64url_to_bytes(challenge),
            expected_origin=ORIGIN,
            expected_rp_id=RP_ID,
            credential_public_key=base64url_to_bytes(cred.public_key),
            credential_current_sign_count=cred.sign_count,
            require_user_verification=False
        )
    except InvalidAuthenticationResponse as e:
        return jsonify({'error': f'Authentication failed: {e}'}), 400

    # Update sign count
    cred.sign_count = verification.new_sign_count
    db.session.commit()

    # Login the user
    user = User.query.get(cred.user_id)
    login_user(user, remember=True)
    
    # Marcamos sesión como válida para saltarse el MFA
    session['mfa_authenticated'] = True
    session.permanent = True # Persistent session

    del session['authentication_challenge']
    
    return jsonify({
        'status': 'ok', 
        'user': {
            'id': user.id,
            'email': user.email,
            'nombre_completo': user.nombre_completo,
            'is_admin': user.is_admin
        }
    })
