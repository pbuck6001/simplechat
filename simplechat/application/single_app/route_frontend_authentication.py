# route_frontend_authentication.py

from config import *
from functions_authentication import _build_msal_app, _load_cache, _save_cache
import logging
from urllib.parse import urlparse, parse_qs, unquote

redirect_uri="http://127.0.0.1:5000/getAToken"
# redirect_uri = "https://simple-chat-app-cjdhfbddh2cmhkd9.azurewebsites.net/getAToken"
# redirect_uri="https://simple-chat-app-cjdhfbddh2cmhkd9.eastus-01.azurewebsites.net/getAToken"
if os.getenv('APP_ENV') == 'local':
    PREFERRED_URL_SCHEME = 'http'
else:
    PREFERRED_URL_SCHEME = 'https'

# Debug function to trace redirect URI
def debug_redirect_uri():
    """Debug function to trace redirect URI configuration"""
    print("\n" + "="*60)
    print("DEBUG: Redirect URI Trace")
    print("="*60)
    
    # 1. Environment variable
    env_redirect = os.environ.get('REDIRECT_URI', 'NOT SET')
    print(f"1. From Environment: {env_redirect}")
    
    # 2. Flask URL generation (if using url_for)
    try:
        with app.test_request_context():
            flask_redirect = url_for('getAToken', _external=True)
            print(f"2. From Flask url_for: {flask_redirect}")
    except Exception as e:
        print(f"2. Flask url_for error: {e}")
    
    # 3. Current request URL
    if request:
        print(f"3. Current request URL: {request.url}")
        print(f"   Host: {request.host}")
        print(f"   Scheme: {request.scheme}")
    
    # 4. Configuration values
    print(f"4. Flask SERVER_NAME: {app.config.get('SERVER_NAME', 'NOT SET')}")
    print(f"   Flask PREFERRED_URL_SCHEME: {app.config.get('PREFERRED_URL_SCHEME', 'NOT SET')}")
    
    print("="*60 + "\n")

@app.route('/debug-me')
def debug_me():
    """Temporary route to see current user info"""
    if 'user' in session:
        import json
        return f"<pre>{json.dumps(session['user'], indent=2)}</pre>"
    else:
        return "Not logged in"

def register_route_frontend_authentication(app):
    @app.route('/login')
    def login():
        # Debug trace
        debug_redirect_uri()
          # This should match your redirect URI in Azure AD app registration
        # Clear potentially stale cache/user info before starting new login
        session.pop("user", None)
        session.pop("token_cache", None)

        # Use helper to build app (cache not strictly needed here, but consistent)
        msal_app = _build_msal_app()

        logging.debug(f"Login redirect_uri: {redirect_uri}")
        print(f"Redirect URI: {redirect_uri}")

        if os.getenv('APP_ENV') == 'local':
            auth_url = msal_app.get_authorization_request_url(
                scopes=SCOPE, # Use SCOPE from config (includes offline_access)
                redirect_uri=redirect_uri
            )
        else:
            auth_url = msal_app.get_authorization_request_url(
                scopes=SCOPE, # Use SCOPE from config (includes offline_access)
                # redirect_uri=url_for('authorized', _external=True, _scheme='https') # Ensure scheme is https if deployed
                redirect_uri=url_for('authorized', _external=True, _scheme='https')
                # redirect_uri=redirect_uri
        )
        logging.debug(f"Auth URL: {auth_url}")
        print(f"Auth URL: {auth_url}")
        print("Redirecting to Azure AD for authentication.")
        #auth_url= auth_url.replace('https://', 'http://')  # Ensure HTTPS for security

        # Debug: Print what we're actually using
        print(f"\nDEBUG - Auth Request Parameters:")
        # print(f"  Client ID: {client_id}")
        # print(f"  Tenant ID: {tenant_id}")
        print(f"  Redirect URI (raw): {redirect_uri}")
        print(f"  Redirect URI (encoded): {quote(redirect_uri)}")

        return redirect(auth_url)

    @app.route('/getAToken') # This is your redirect URI path
    def authorized():
        # Check for errors passed back from Azure AD
        if request.args.get('error'):
            error = request.args.get('error')
            error_description = request.args.get('error_description', 'No description provided.')
            print(f"Azure AD Login Error: {error} - {error_description}")
            return f"Login Error: {error} - {error_description}", 400 # Or render an error page

        logging.debug(f"Callback redirect_uri: {redirect_uri}")
        print(f"Callback redirect_uri: {redirect_uri}")

        code = request.args.get('code')
        if not code:
            print("Authorization code not found in callback.")
            return "Authorization code not found", 400

        # Build MSAL app WITH session cache (will be loaded by _build_msal_app via _load_cache)
        msal_app = _build_msal_app(cache=_load_cache()) # Load existing cache

        if os.getenv('APP_ENV') == 'local':
            result = msal_app.acquire_token_by_authorization_code(
                        code=code,
                        scopes=SCOPE, # Request the same scopes again
                        # redirect_uri=url_for('authorized', _external=True, _scheme='https')
                        # redirect_uri=url_for('authorized', _external=True, _scheme='http')
                        redirect_uri=redirect_uri
                        )
        else:
            result = msal_app.acquire_token_by_authorization_code(
                code=code,
                scopes=SCOPE, # Request the same scopes again
                redirect_uri=url_for('authorized', _external=True, _scheme='https')
                # redirect_uri=url_for('authorized', _external=True, _scheme='http')
                # redirect_uri=redirect_uri
            )

        if "error" in result:
            error_description = result.get("error_description", result.get("error"))
            print(f"Token acquisition failure: {error_description}")
            return f"Login failure: {error_description}", 500

        # --- Store results ---
        # Store user identity info (claims from ID token)
        session["user"] = result.get("id_token_claims")
        # DO NOT store access/refresh token directly in session anymore

        # --- CRITICAL: Save the entire cache (contains tokens) to session ---
        _save_cache(msal_app.token_cache)

        print(f"User {session['user'].get('name')} logged in successfully.")
        # Redirect to the originally intended page or home
        # You might want to store the original destination in the session during /login
        return redirect(url_for('index')) # Or another appropriate page

    # This route is for API calls that need a token, not the web app login flow. This does not kick off a session.
    @app.route('/getATokenApi') # This is your redirect URI path
    def authorized_api():
        # Check for errors passed back from Azure AD
        if request.args.get('error'):
            error = request.args.get('error')
            error_description = request.args.get('error_description', 'No description provided.')
            print(f"Azure AD Login Error: {error} - {error_description}")
            return f"Login Error: {error} - {error_description}", 400 # Or render an error page

        code = request.args.get('code')
        if not code:
            print("Authorization code not found in callback.")
            return "Authorization code not found", 400

        # Build MSAL app WITH session cache (will be loaded by _build_msal_app via _load_cache)
        msal_app = _build_msal_app(cache=_load_cache()) # Load existing cache

        if os.getenv('APP_ENV') == 'local':
            result = msal_app.acquire_token_by_authorization_code(
                code=code,
                scopes=SCOPE, # Request the same scopes again
                redirect_uri=redirect_uri
            )
        else:
            result = msal_app.acquire_token_by_authorization_code(
                code=code,
                scopes=SCOPE, # Request the same scopes again
                redirect_uri=url_for('authorized', _external=True, _scheme='https')
                # redirect_uri=url_for('authorized', _external=True, _scheme='http')
        )

        if "error" in result:
            error_description = result.get("error_description", result.get("error"))
            print(f"Token acquisition failure: {error_description}")
            return f"Login failure: {error_description}", 500

        return jsonify(result, 200)

    @app.route('/logout')
    def logout():
        user_name = session.get("user", {}).get("name", "User")
        # Get the user's email before clearing the session
        user_email = session.get("user", {}).get("preferred_username") or session.get("user", {}).get("email")
        # Clear Flask session data
        session.clear()
        # Redirect user to Azure AD logout endpoint
        # MSAL provides a helper for this too, but constructing manually is fine
        logout_uri = url_for('index', _external=True, _scheme='https') # Where to land after logout
        logout_url = (
            f"{AUTHORITY}/oauth2/v2.0/logout"
            f"?post_logout_redirect_uri={quote(logout_uri)}"
        )
        # Add logout_hint parameter if we have the user's email
        if user_email:
            logout_url += f"&logout_hint={quote(user_email)}"
        
        print(f"{user_name} logged out. Redirecting to Azure AD logout.")
        return redirect(logout_url)