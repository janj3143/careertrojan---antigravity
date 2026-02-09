import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

# Add services directory to path
services_path = Path(__file__).parent.parent / "services"
sys.path.insert(0, str(services_path))

from email_verification_service import get_email_verification_service
from two_factor_auth_service import get_2fa_service

st.set_page_config(page_title="Verify Your Account", page_icon="✅")
st.title("✅ Account Verification")

# Get services
email_service = get_email_verification_service()
twofa_service = get_2fa_service()

# Get user info from session
user_email = st.session_state.get("user_email", "Unknown User")
user_name = st.session_state.get("user_name", st.session_state.get("username", "User"))

st.caption(f"👤 Logged in as: **{user_email}**")

# Check URL parameters for verification token
query_params = st.query_params
if "verify_email" in query_params:
    verification_token = query_params["verify_email"]

    with st.spinner("Verifying your email..."):
        success, message = email_service.verify_token(verification_token)

        if success:
            st.session_state["email_verified"] = True
            st.balloons()
            st.success(f"🎉 {message}")
        else:
            st.error(f"❌ {message}")

# Email Verification Section
st.markdown("### 📧 Email Verification")

# Check verification status
verification_status = email_service.get_verification_status(user_email)
is_verified = email_service.is_email_verified(user_email)

if is_verified:
    st.success("✅ Your email has been successfully verified!")

    if verification_status['verified_at']:
        st.info(f"Verified on: {verification_status['verified_at']}")
else:
    st.warning("⚠️ Your email address is not yet verified.")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📧 Send Verification Email", type="primary"):
            with st.spinner("Sending verification email..."):
                success, message = email_service.send_verification_email(
                    user_email,
                    user_name
                )

                if success:
                    st.success(message)
                    st.info(f"📬 Check your email: **{user_email}**")
                    st.info(f"⏰ Link expires in {email_service.config['token_expiry_hours']} hours")
                else:
                    st.error(message)

    with col2:
        if verification_status['token']:
            if st.button("🔄 Resend Verification Email"):
                with st.spinner("Resending verification email..."):
                    success, message = email_service.resend_verification_email(
                        user_email,
                        user_name
                    )

                    if success:
                        st.success(message)
                    else:
                        st.error(message)

    # Show verification status details
    if verification_status['token']:
        with st.expander("📋 Verification Status Details"):
            status_col1, status_col2 = st.columns(2)

            with status_col1:
                st.metric("Status", "Pending" if not verification_status['verified'] else "Verified")
                if verification_status['created_at']:
                    st.caption(f"Sent: {verification_status['created_at']}")

            with status_col2:
                if verification_status['is_expired']:
                    st.metric("Token Status", "❌ Expired")
                else:
                    st.metric("Token Status", "✅ Active")
                if verification_status['expires_at']:
                    st.caption(f"Expires: {verification_status['expires_at']}")

st.markdown("---")

# Two-Factor Authentication Section
st.markdown("### 🔐 Two-Factor Authentication (2FA)")

# Get 2FA status
twofa_status = twofa_service.get_2fa_status(user_email)
is_2fa_enabled = twofa_service.is_2fa_enabled(user_email)

if is_2fa_enabled:
    st.success("✅ Two-Factor Authentication is **ENABLED** for your account!")
    st.info("🛡️ Your account has an extra layer of security")

    if twofa_status['enabled_at']:
        st.caption(f"Enabled on: {twofa_status['enabled_at']}")

    # Recovery codes info
    if twofa_status['recovery_codes_remaining'] > 0:
        st.info(f"📋 You have **{twofa_status['recovery_codes_remaining']} unused recovery codes**")
    else:
        st.warning("⚠️ No recovery codes remaining! Generate new ones to maintain account access.")

    # Disable 2FA option
    with st.expander("🔓 Disable Two-Factor Authentication"):
        st.warning("**Warning:** Disabling 2FA will reduce your account security.")

        disable_code = st.text_input(
            "Enter your 6-digit authenticator code or recovery code",
            max_chars=10,
            key="disable_2fa_code"
        )

        col_disable1, col_disable2 = st.columns(2)

        with col_disable1:
            if st.button("🔓 Disable 2FA", type="secondary"):
                if disable_code:
                    with st.spinner("Disabling 2FA..."):
                        success, message = twofa_service.disable_2fa(user_email, disable_code)

                        if success:
                            st.session_state["enable_2fa"] = False
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                else:
                    st.error("Please enter a verification code.")

else:
    st.info("� Two-Factor Authentication is currently **DISABLED**")
    st.warning("⚠️ Enable 2FA to add an extra layer of security to your account")

    # 2FA Setup Wizard
    setup_tab1, setup_tab2, setup_tab3 = st.tabs([
        "1️⃣ Scan QR Code",
        "2️⃣ Verify Setup",
        "3️⃣ Save Recovery Codes"
    ])

    with setup_tab1:
        st.markdown("#### Step 1: Scan QR Code with Authenticator App")

        st.info("""
        📱 **Compatible Authenticator Apps:**
        - Google Authenticator (iOS/Android)
        - Microsoft Authenticator (iOS/Android)
        - Authy (iOS/Android/Desktop)
        - 1Password
        - LastPass Authenticator
        """)

        if st.button("🎯 Generate QR Code", type="primary"):
            with st.spinner("Generating QR code..."):
                # Generate QR code
                qr_base64 = twofa_service.generate_qr_code(user_email)

                # Get secret for manual entry
                uri = twofa_service.get_totp_uri(user_email)
                secrets_data = twofa_service._load_secrets()
                secret = secrets_data[user_email]['secret']

                # Display QR code
                st.markdown("### 📱 Scan this QR Code")
                st.image(f"data:image/png;base64,{qr_base64}", width=300)

                st.success("✅ QR Code generated! Scan it with your authenticator app.")

                # Show manual entry option
                with st.expander("� Can't scan? Enter manually"):
                    st.code(secret)
                    st.caption(f"**Account:** {user_email}")
                    st.caption(f"**Issuer:** {twofa_service.issuer_name}")
                    st.caption("**Type:** Time-based")

                # Store in session that QR was generated
                st.session_state["2fa_qr_generated"] = True

    with setup_tab2:
        st.markdown("#### Step 2: Verify Your Setup")

        if not st.session_state.get("2fa_qr_generated", False):
            st.warning("⚠️ Please generate and scan the QR code in Step 1 first")
        else:
            st.info("Enter the 6-digit code from your authenticator app to verify setup")

            verify_code = st.text_input(
                "6-Digit Code",
                max_chars=6,
                key="verify_2fa_code",
                placeholder="000000"
            )

            col_verify1, col_verify2 = st.columns(2)

            with col_verify1:
                if st.button("✅ Verify & Enable 2FA", type="primary"):
                    if verify_code and len(verify_code) == 6:
                        with st.spinner("Verifying code..."):
                            success, message = twofa_service.enable_2fa(user_email, verify_code)

                            if success:
                                st.session_state["enable_2fa"] = True
                                st.session_state["2fa_setup_complete"] = True
                                st.balloons()
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
                    else:
                        st.error("Please enter a valid 6-digit code")

            with col_verify2:
                # Show current code in dev mode for testing
                if st.session_state.get("dev_mode", False):
                    current_code = twofa_service.get_current_totp_code(user_email)
                    if current_code:
                        st.info(f"🧪 **Test Code:** {current_code}")
                        st.caption("(Dev mode only)")

    with setup_tab3:
        st.markdown("#### Step 3: Save Your Recovery Codes")

        if not st.session_state.get("2fa_setup_complete", False):
            st.warning("⚠️ Please complete Step 2 (verify setup) first")
        else:
            st.info("""
            🔑 **Recovery codes** let you access your account if you lose your phone or authenticator app.

            **Important:**
            - Each code can only be used once
            - Store them in a safe place (password manager, safe, etc.)
            - Don't share them with anyone
            """)

            if st.button("📋 Generate Recovery Codes", type="primary"):
                with st.spinner("Generating recovery codes..."):
                    recovery_codes = twofa_service.generate_recovery_codes(user_email)

                    st.success("✅ Recovery codes generated!")
                    st.warning("⚠️ **SAVE THESE NOW!** They will not be shown again.")

                    # Display codes in a grid
                    st.markdown("### 🔐 Your Recovery Codes")

                    code_col1, code_col2 = st.columns(2)

                    for i, code in enumerate(recovery_codes):
                        with code_col1 if i % 2 == 0 else code_col2:
                            st.code(code, language=None)

                    # Download option
                    codes_text = "\n".join([f"{i+1}. {code}" for i, code in enumerate(recovery_codes)])
                    download_content = f"""
IntelliCV Account Recovery Codes
Account: {user_email}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

IMPORTANT: Keep these codes in a safe place!
Each code can only be used once.

{codes_text}

If you lose access to your authenticator app, you can use one of these codes to log in.
After using a code, it will be marked as used and cannot be reused.
"""

                    st.download_button(
                        label="💾 Download Recovery Codes",
                        data=download_content,
                        file_name=f"intellicv_recovery_codes_{user_email.split('@')[0]}.txt",
                        mime="text/plain"
                    )

                    st.session_state["recovery_codes_saved"] = True

# Show recovery code usage
if is_2fa_enabled and twofa_status['recovery_codes_generated']:
    with st.expander("📋 Recovery Code Management"):
        total_codes = 10  # Default count
        used_codes = total_codes - twofa_status['recovery_codes_remaining']

        st.progress(twofa_status['recovery_codes_remaining'] / total_codes)
        st.metric("Remaining Recovery Codes", twofa_status['recovery_codes_remaining'])

        if twofa_status['recovery_codes_remaining'] < 3:
            st.warning("⚠️ Running low on recovery codes!")

        if st.button("🔄 Generate New Recovery Codes"):
            st.warning("Generating new codes will invalidate all existing recovery codes.")
            if st.button("✅ Confirm - Generate New Codes"):
                new_codes = twofa_service.generate_recovery_codes(user_email)
                st.success("✅ New recovery codes generated!")

                # Display new codes
                for code in new_codes:
                    st.code(code, language=None)

st.markdown("---")

# Account Security Overview
st.markdown("### �️ Account Security Overview")

sec_col1, sec_col2, sec_col3 = st.columns(3)

with sec_col1:
    st.metric(
        "Email Verification",
        "✅ Verified" if is_verified else "⚠️ Pending",
        delta="Secure" if is_verified else "Action Required",
        delta_color="normal" if is_verified else "off"
    )

with sec_col2:
    st.metric(
        "Two-Factor Auth",
        "🔒 Enabled" if st.session_state.get("enable_2fa") else "🔓 Disabled",
        delta="Coming Soon",
        delta_color="off"
    )

with sec_col3:
    st.metric(
        "Account Status",
        "🟢 Active",
        delta="Good Standing"
    )

# Security Tips
with st.expander("🔐 Security Best Practices"):
    st.markdown("""
    **Protect Your Account:**

    1. ✅ **Verify your email** - Essential for account recovery
    2. 🔐 **Enable 2FA** - Adds an extra layer of security (coming soon)
    3. 🔑 **Use a strong password** - Mix of letters, numbers, and symbols
    4. 🚫 **Don't share credentials** - Keep your login information private
    5. 📱 **Monitor account activity** - Check for suspicious logins
    6. 🔄 **Regular password updates** - Change your password periodically

    **Why Email Verification Matters:**
    - 🛡️ Protects against unauthorized access
    - 📧 Enables password recovery
    - ✅ Required for premium features and payments
    - 🔔 Allows important account notifications
    """)

st.markdown("---")

# Developer/Debug Section (ADMIN ONLY - not visible to regular users)
if st.session_state.get("user_role") == "admin" and st.checkbox("🔧 Admin Developer Tools", value=False):
    st.markdown("### 🛑️ Admin Developer Tools")
    st.caption("⚠️ Admin access only - not visible to regular users")

    dev_tab1, dev_tab2, dev_tab3 = st.tabs(["📊 Verification Stats", "🧪 Session State", "⚙️ Service Config"])

    with dev_tab1:
        st.markdown("#### Email Verification Statistics")
        stats = email_service.get_verification_stats()

        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)

        with stat_col1:
            st.metric("Total Tokens", stats['total_tokens'])
        with stat_col2:
            st.metric("Verified", stats['verified_count'])
        with stat_col3:
            st.metric("Pending", stats['pending_count'])
        with stat_col4:
            st.metric("Expired", stats['expired_count'])

        st.metric("Verification Rate", f"{stats['verification_rate']:.1f}%")

        if st.button("🧹 Cleanup Expired Tokens"):
            cleaned = email_service.cleanup_expired_tokens()
            st.success(f"Cleaned up {cleaned} expired tokens")

    with dev_tab2:
        st.markdown("#### Session State")
        st.json(dict(st.session_state))

    with dev_tab3:
        st.markdown("#### Email Service Configuration")
        config_display = {
            'SMTP Server': email_service.config['smtp_server'],
            'SMTP Port': email_service.config['smtp_port'],
            'From Email': email_service.config['from_email'],
            'From Name': email_service.config['from_name'],
            'Base URL': email_service.config['base_url'],
            'Token Expiry (hours)': email_service.config['token_expiry_hours'],
            'Configured': bool(email_service.config['smtp_username'] and email_service.config['smtp_password'])
        }
        st.json(config_display)
