# app.py
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- Flask App Configuration ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here' # *** IMPORTANT: Change this to a random, secret key ***
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db' # Using a SQLite database file
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Disable this to save resources

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login' # Set the view function name for the login page
login_manager.login_message_category = 'info' # Category for flash messages

# Updated color palette to match the new design
COLORS = [
    '#7C6F65', '#A69989', '#DAC6B5', '#8D7B6D', '#B5A898',
    '#C4B5A5', '#9F8E82', '#E8E1D9', '#D3C5B8', '#B8A99A'
]

# --- Database Model ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

# --- Flask-Login User Loader ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Routes ---

@app.route('/')
@login_required # Protect this route - requires login
def index():
    # Pass user information to the template
    return render_template('index.html', user=current_user)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Basic validation
        if not username or not email or not password:
            # You might want to add more specific validation and feedback
            return render_template('signup.html', error="All fields are required.")

        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return render_template('signup.html', error="Username already exists.")
        
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            return render_template('signup.html', error="Email already exists.")


        # Hash password
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256') # Use a secure hashing method

        # Create new user
        new_user = User(username=username, email=email, password=hashed_password)

        # Add user to database
        db.session.add(new_user)
        db.session.commit()

        # Redirect to login page after successful signup
        # You might want to flash a success message here
        return redirect(url_for('login'))

    # Render signup form on GET request
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember') # Check if "Remember Me" was checked

        user = User.query.filter_by(email=email).first()

        # Check if user exists and password is correct
        if user and check_password_hash(user.password, password):
            login_user(user, remember=remember)
            # Redirect to the page the user was trying to access, or index if none
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            # You might want to flash an error message here
            return render_template('login.html', error="Invalid email or password.")

    # Render login form on GET request
    return render_template('login.html')

@app.route('/logout')
@login_required # Ensure only logged-in users can logout (optional, but good practice)
def logout():
    logout_user()
    # You might want to flash a success message here
    return redirect(url_for('login')) # Redirect to login page after logout


# --- Existing Data Visualization Functions (Keep these) ---

def create_chart(df, chart_type, x_column, y_column):
    # ... (Your existing create_chart function code) ...
    if chart_type == 'bar':
        fig = go.Figure(data=[
            go.Bar(
                x=df[x_column],
                y=df[y_column],
                marker_color=COLORS[0],
                marker_line_color=COLORS[2],
                marker_line_width=1.5,
                opacity=0.9
            )
        ])

        # Add 3D effect to bar chart
        fig.update_layout(
            scene=dict(
                camera=dict(
                    up=dict(x=0, y=0, z=1),
                    center=dict(x=0, y=0, z=0),
                    eye=dict(x=1.5, y=1.5, z=1.5)
                )
            )
        )

    elif chart_type == 'line':
        fig = go.Figure(data=[
            go.Scatter(
                x=df[x_column],
                y=df[y_column],
                mode='lines+markers',
                line=dict(
                    color=COLORS[0],
                    width=3,
                    shape='spline',
                    smoothing=1.3
                ),
                marker=dict(
                    size=8,
                    color=COLORS[1],
                    line=dict(
                        color=COLORS[2],
                        width=2
                    )
                ),
                fill='tonexty',
                fillcolor=f'rgba(124, 111, 101, 0.1)'
            )
        ])

    elif chart_type == 'pie':
        fig = go.Figure(data=[
            go.Pie(
                labels=df[x_column],
                values=df[y_column],
                hole=.4,
                marker_colors=COLORS,
                textinfo='label+percent',
                textposition='outside',
                textfont=dict(size=14, family='Poppins'),
                pull=[0.05] * len(df[x_column]),
                rotation=90
            )
        ])

    # Common layout updates (Make sure to fix the `var(--...)` issues here as discussed)
    fig.update_layout(
        title=dict(
            text=f'{chart_type.title()} Chart: {y_column} by {x_column}',
            font=dict(
                family='Poppins', # Use string literal
                size=24,
                color=COLORS[0] # Use actual color from COLORS list
            ),
            x=0.5,
            y=0.95
        ),
        paper_bgcolor='rgba(250,247,242,0.5)',
        plot_bgcolor='rgba(250,247,242,0.5)',
        font=dict(
            family='Inter, sans-serif', # Use string literal
            size=12,
            color=COLORS[0] # Use actual color
        ),
        margin=dict(t=100, l=50, r=50, b=50),
        showlegend=True if chart_type == 'pie' else False, # Show legend for pie only
        legend=dict(
            bgcolor='rgba(255,255,255,0.9)',
            bordercolor=COLORS[2], # Use actual color
            borderwidth=1
        ),
        xaxis=dict(
            title=dict(
                text=x_column,
                font=dict(size=14)
            ),
            gridcolor='rgba(166, 153, 137, 0.1)',
            showline=True,
            linewidth=2,
            linecolor=COLORS[2], # Use actual color
            zeroline=False
        ),
        yaxis=dict(
            title=dict(
                text=y_column,
                font=dict(size=14)
            ),
            gridcolor='rgba(166, 153, 137, 0.1)',
            showline=True,
            linewidth=2,
            linecolor=COLORS[2], # Use actual color
            zeroline=False
        )
    )

    # Add hover effects
    fig.update_traces(
        hoverinfo='all',
        hovertemplate="<b>%{x}</b><br>" +
                      "%{y}<br>" +
                      "<extra></extra>"
    )


    return fig


# You will keep your /upload and /visualize routes, but modify them
# if you need to associate uploads/visualizations with a specific user.
# For now, they can remain as is, operating on uploaded data per session.
# If you want to save user data permanently, you'll need to modify these.

@app.route('/upload', methods=['POST'])
@login_required # Protect this route
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    try:
        if file.filename.endswith('.csv'):
            # Read as string to avoid potential type issues with mixed data
            df = pd.read_csv(file, dtype=str)
        elif file.filename.endswith(('.xlsx', '.xls')):
             # Note: Excel reading is still client-side according to index.html's alert.
             # If you want server-side Excel reading, you'll need pandas and potentially openpyxl.
             # For this example, we'll assume CSV for server-side processing.
            return jsonify({'error': 'Server-side Excel processing not fully implemented in this example.'}), 400
        else:
            return jsonify({'error': 'Unsupported file format'}), 400

        # Analyze column types after reading
        column_types = analyze_column_types(df)

        # In a real app, you might save the file or its data associated with current_user.id
        # For this example, we are just processing and returning column info.

        return jsonify({
            'columns': list(df.columns),
            'types': column_types,
            'success': True
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

def analyze_column_types(df):
    column_types = {}
    for column in df.columns:
        # Attempt to convert to numeric, if successful, it's numeric 'N'
        try:
            # Try converting to numeric, coercing errors means non-numeric become NaN
            numeric_col = pd.to_numeric(df[column], errors='coerce')
            # If most values are numeric (e.g., less than 50% are NaN), consider it numeric
            if numeric_col.notna().sum() / len(df) > 0.5: # Threshold to consider a column numeric
                 column_types[column] = 'N'
            else:
                 # Otherwise, check if it contains both text and numbers
                 if df[column].astype(str).str.contains(r'[A-Za-z]').any() and \
                    df[column].astype(str).str.contains(r'[0-9]').any():
                     column_types[column] = 'TN' # Text and Number
                 else:
                     column_types[column] = 'T' # Text only
        except:
             # If conversion fails entirely, it's text or mixed
             if df[column].dtype == 'object':
                 if df[column].astype(str).str.contains(r'[A-Za-z]').any() and \
                    df[column].astype(str).str.contains(r'[0-9]').any():
                     column_types[column] = 'TN'
                 else:
                     column_types[column] = 'T'
             else:
                 # Handle other dtypes if necessary, default to Text for safety
                 column_types[column] = 'T'
    return column_types


@app.route('/visualize', methods=['POST'])
@login_required # Protect this route
def create_visualization():
    # In a real app, you might load data associated with the current_user
    # instead of expecting the file again. For this example, we still
    # expect the file in the request, which is not ideal for a real app
    # after login and upload. A better approach is to save the file/data
    # server-side on /upload and then reference it by ID on /visualize.

    if 'file' not in request.files:
         # If not receiving the file again, you'd load data by user or ID
         # For this example, we'll assume the file is still sent for simplicity,
         # but acknowledge this is not the best approach with login.
        return jsonify({'error': 'No file provided'}), 400 # Error if file is missing

    file = request.files['file']
    chart_type = request.form.get('chartType')
    x_column = request.form.get('xColumn')
    y_column = request.form.get('yColumn')

    try:
        if file.filename.endswith('.csv'):
             # Read as string to maintain original data for plotting labels
            df = pd.read_csv(file, dtype=str)
        elif file.filename.endswith(('.xlsx', '.xls')):
             return jsonify({'error': 'Server-side Excel processing not fully implemented in this example.'}), 400
        else:
             return jsonify({'error': 'Unsupported file format'}), 400


        fig = create_chart(df, chart_type, x_column, y_column)
        return jsonify({'plot': fig.to_json()})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# --- Run the App ---
if __name__ == '__main__':
    # This is a one-time step to create the database and tables.
    # Run this once, then you can just run app.py normally.
    with app.app_context():
        db.create_all()
    app.run(debug=True) # Set debug=False in production