def login_page():
    """Modern login page matching the screenshot design"""
    
    # Set page config for centered layout
    if not st.session_state.get('page_config_set', False):
        st.set_page_config(
            page_title="MultiAgentAI21",
            page_icon="🤖",
            layout="centered",
            initial_sidebar_state="collapsed",
        )
        st.session_state.page_config_set = True

    # Custom CSS for the modern login design
    st.markdown(
        """
        <style>
        /* Hide Streamlit default elements */
        .stApp > header {visibility: hidden;}
        .block-container {padding: 0 !important; max-width: 100% !important;}
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Background */
        .stApp {
            background: #e8f4f8;
            min-height: 100vh;
        }
        
        /* Main container */
        .main > div {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 1rem;
        }
        
        /* Login card container */
        [data-testid="stVerticalBlock"] > div:has(.login-header) {
            background: white;
            border-radius: 12px;
            padding: 3rem;
            max-width: 450px;
            width: 100%;
            margin: 0 auto;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
        }
        
        /* Header styling */
        .login-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .login-header h1 {
            font-size: 2.5rem;
            font-weight: 700;
            color: #1a1a1a;
            margin: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        
        /* Lock icon */
        .lock-icon {
            font-size: 3rem;
            margin-bottom: 0.5rem;
        }
        
        /* Toggle switch container */
        .toggle-container {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.75rem;
            margin: 1.5rem 0 2rem 0;
            font-size: 0.95rem;
            color: #4a5568;
        }
        
        /* Welcome text */
        .welcome-text {
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .welcome-text h2 {
            font-size: 1.75rem;
            font-weight: 600;
            color: #1a1a1a;
            margin: 0 0 0.5rem 0;
        }
        
        .welcome-text p {
            color: #6b7280;
            font-size: 0.95rem;
            margin: 0;
        }
        
        /* Tabs styling */
        .stTabs {
            margin-bottom: 2rem;
        }
        
        .stTabs [data-baseweb="tab-list"] {
            background: transparent;
            gap: 2rem;
            border-bottom: 2px solid #e5e7eb;
            padding: 0;
        }
        
        .stTabs [data-baseweb="tab"] {
            background: transparent;
            border: none;
            color: #6b7280;
            font-weight: 500;
            font-size: 1rem;
            padding: 0.75rem 0;
            border-bottom: 2px solid transparent;
            margin-bottom: -2px;
        }
        
        .stTabs [aria-selected="true"] {
            color: #f97316 !important;
            border-bottom: 2px solid #f97316 !important;
        }
        
        /* Input fields */
        .stTextInput > label {
            color: #374151;
            font-weight: 500;
            font-size: 0.875rem;
            margin-bottom: 0.5rem;
        }
        
        .stTextInput > div > div > input {
            background: #fef3f2 !important;
            border: 1px solid #fee2e2 !important;
            border-radius: 8px !important;
            padding: 0.75rem 1rem !important;
            font-size: 1rem !important;
            color: #1a1a1a !important;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #f97316 !important;
            outline: none !important;
            box-shadow: 0 0 0 3px rgba(249, 115, 22, 0.1) !important;
        }
        
        /* Password field with icon */
        .stTextInput:has(input[type="password"]) {
            position: relative;
        }
        
        /* Forgot password link */
        .forgot-password-container {
            text-align: right;
            margin: 0.5rem 0 1.5rem 0;
        }
        
        .forgot-password-container a {
            color: #3b82f6;
            text-decoration: none;
            font-size: 0.875rem;
            font-weight: 500;
        }
        
        .forgot-password-container a:hover {
            text-decoration: underline;
        }
        
        /* Buttons */
        .stButton > button {
            background: #4f46e5 !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 0.75rem !important;
            font-size: 1rem !important;
            font-weight: 500 !important;
            width: 100% !important;
            margin: 0.5rem 0 !important;
            cursor: pointer !important;
            transition: background 0.2s ease !important;
        }
        
        .stButton > button:hover {
            background: #4338ca !important;
        }
        
        /* Social buttons */
        .social-button {
            width: 100%;
            padding: 0.75rem;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 500;
            border: none;
            cursor: pointer;
            transition: all 0.2s ease;
            margin: 0.5rem 0;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
        }
        
        .github-button {
            background: #6366f1;
            color: white;
        }
        
        .github-button:hover {
            background: #5558e3;
        }
        
        .google-button {
            background: #7c3aed;
            color: white;
        }
        
        .google-button:hover {
            background: #6d28d9;
        }
        
        /* Sign up link */
        .signup-link {
            text-align: center;
            margin-top: 2rem;
            color: #6b7280;
            font-size: 0.875rem;
        }
        
        .signup-link a {
            color: #3b82f6;
            text-decoration: none;
            font-weight: 500;
        }
        
        .signup-link a:hover {
            text-decoration: underline;
        }
        
        /* Hide streamlit elements */
        .css-1y4p8pa {max-width: none !important;}
        .css-12oz5g7 {padding: 0 !important;}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Create centered container
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Header with lock icon
        st.markdown(
            """
            <div class="login-header">
                <div class="lock-icon">🔒</div>
                <h1>Login or Sign Up</h1>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Tabs for Login and Sign Up
        login_tab, signup_tab = st.tabs(["Login", "Sign Up"])

        with login_tab:
            # Welcome text
            st.markdown(
                """
                <div class="welcome-text">
                    <h2>Login to your account</h2>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Login form
            email = st.text_input("Email", key="login_email", placeholder="Enter your email")
            password = st.text_input("Password", type="password", key="login_password", placeholder="Enter your password")
            
            # Forgot password link
            st.markdown(
                """
                <div class="forgot-password-container">
                    <a href="#">Forgot password?</a>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Login button
            if st.button("Login", key="login_button", use_container_width=True):
                if email and password:
                    user, message = authenticate_user(email, password)
                    if user:
                        st.session_state["authenticated"] = True
                        st.session_state["user_email"] = email
                        st.session_state["user_uid"] = user.uid
                        st.session_state["auth_message"] = "Login successful!"
                        st.success("✅ Login successful!")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.error("❌ Please enter both email and password.")

            # Divider
            st.markdown("<hr style='margin: 2rem 0; border: none; border-top: 1px solid #e5e7eb;'>", unsafe_allow_html=True)

            # Social login buttons
            st.markdown(
                """
                <button class="social-button github-button">
                    Sign in with GitHub
                </button>
                """,
                unsafe_allow_html=True
            )
            
            st.markdown(
                """
                <button class="social-button google-button">
                    Sign in with Google
                </button>
                """,
                unsafe_allow_html=True
            )

            # Sign up link
            st.markdown(
                """
                <div class="signup-link">
                    Don't have an account? <a href="#" onclick="document.querySelector('[data-baseweb=tab]:nth-child(2)').click()">Sign up</a>
                </div>
                """,
                unsafe_allow_html=True
            )

        with signup_tab:
            # Welcome text for signup
            st.markdown(
                """
                <div class="welcome-text">
                    <h2>Create your account</h2>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            new_email = st.text_input("Email", key="signup_email", placeholder="Enter your email")
            new_password = st.text_input("Password", type="password", key="signup_password", placeholder="Create a password")
            confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password", placeholder="Confirm your password")

            if st.button("Sign Up", key="signup_button", use_container_width=True):
                if new_email and new_password and confirm_password:
                    if new_password == confirm_password:
                        if len(new_password) >= 6:
                            user, message = create_user(new_email, new_password)
                            if user:
                                st.success(f"✅ {message}")
                                # Optionally auto-login after signup
                                st.session_state["authenticated"] = True
                                st.session_state["user_email"] = new_email
                                st.session_state["user_uid"] = user.uid
                                st.session_state["auth_message"] = "Account created and logged in!"
                                st.rerun()
                            else:
                                st.error(f"❌ {message}")
                        else:
                            st.error("❌ Password must be at least 6 characters long.")
                    else:
                        st.error("❌ Passwords do not match.")
                else:
                    st.error("❌ Please fill in all fields.")

            # Divider
            st.markdown("<hr style='margin: 2rem 0; border: none; border-top: 1px solid #e5e7eb;'>", unsafe_allow_html=True)

            # Social signup buttons
            st.markdown(
                """
                <button class="social-button github-button">
                    Sign up with GitHub
                </button>
                """,
                unsafe_allow_html=True
            )
            
            st.markdown(
                """
                <button class="social-button google-button">
                    Sign up with Google
                </button>
                """,
                unsafe_allow_html=True
            )

            # Login link
            st.markdown(
                """
                <div class="signup-link">
                    Already have an account? <a href="#" onclick="document.querySelector('[data-baseweb=tab]:nth-child(1)').click()">Login</a>
                </div>
                """,
                unsafe_allow_html=True
            )