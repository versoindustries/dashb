import os
import openai
from flask import Flask, render_template, url_for, flash, redirect, request, abort, jsonify
from models import db
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from forms import OpenAIForm

from forms import RegistrationForm, LoginForm, SystemPromptForm
from models import User, Conversation, SystemPrompt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

conversation_history = []

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
@app.route("/home")
@login_required
def home():
    return render_template('home.html', title='Home')

@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        api_key = form.api_key.data
        user = User(username=form.username.data, email=form.email.data, password=hashed_password, api_key=api_key)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/manage_api_keys", methods=['GET', 'POST'])
@login_required
def manage_api_keys():
    if not current_user.is_admin:
        abort(403)  # Forbidden

    users = User.query.all()
    return render_template('manage_api_keys.html', title='Manage API Keys', users=users)

def get_openai_response(prompt, api_key):
    import openai

    openai.api_key = api_key
    conversation_history.append({
        "role": "user",
        "content": prompt
    })
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=conversation_history
    )
    conversation_history.append({
        "role": "assistant",
        "content": response.choices[0].message['content'].strip()
    })
    # Ensure the conversation history doesn't exceed 8000 characters
    while sum(len(m["content"]) for m in conversation_history) > 8000:
        conversation_history.pop(0)
    return response.choices[0].message['content'].strip()

@app.route("/branchedchat", methods=['GET'])
@login_required
def branchedchat():
    form = OpenAIForm()
    return render_template('branchedchat.html', title='OpenAI', form=form)

@app.route("/api_chat", methods=['POST'])
@login_required
def api_chat():
    print("API Chat route called")  # Add this line
    data = request.get_json()
    prompt = data.get('message')
    response_text = get_openai_response(prompt, current_user.api_key)
    print(f"Returning response: {response_text}")
    return jsonify(response=response_text)



@app.route("/manage_system_prompts", methods=['GET', 'POST'])
@login_required
def manage_system_prompts():
    if not current_user.is_admin:
        abort(403)  # Forbidden

    form = SystemPromptForm()
    if form.validate_on_submit():
        prompt = form.prompt.data
        new_prompt = SystemPrompt(prompt=prompt)
        db.session.add(new_prompt)
        db.session.commit()
        flash('System prompt added successfully', 'success')

    prompts = SystemPrompt.query.all()
    return render_template('manage_system_prompts.html', title='Manage System Prompts', form=form, prompts=prompts)

@app.route("/edit_system_prompt/<int:prompt_id>", methods=['GET', 'POST'])
@login_required
def edit_system_prompt(prompt_id):
    if not current_user.is_admin:
        abort(403)  # Forbidden

    prompt = SystemPrompt.query.get_or_404(prompt_id)
    form = SystemPromptForm()
    if form.validate_on_submit():
        prompt.prompt = form.prompt.data
        db.session.commit()
        flash('System prompt updated successfully', 'success')
        return redirect(url_for('manage_system_prompts'))

    form.prompt.data = prompt.prompt
    return render_template('edit_system_prompt.html', title='Edit System Prompt', form=form, prompt_id=prompt_id)


@app.route("/delete_system_prompt/<int:prompt_id>", methods=['POST'])
@login_required
def delete_system_prompt(prompt_id):
    if not current_user.is_admin:
        abort(403)  # Forbidden

    prompt = SystemPrompt.query.get_or_404(prompt_id)
    db.session.delete(prompt)
    db.session.commit()
    flash('System prompt deleted successfully', 'success')
    return redirect(url_for('manage_system_prompts'))

@app.route("/web_browsing", methods=['GET', 'POST'])
@login_required
def web_browsing():
    search_results = None
    if request.method == 'POST':
        search_query = request.form['search_query']

        # Get the current working directory
        current_directory = os.getcwd()

        # Construct the path to the ChromeDriver executable
        chromedriver_path = os.path.join(current_directory, "chromedriver")

        # Create a webdriver.Chrome instance with the specified path
        driver = webdriver.Chrome(executable_path=chromedriver_path)

        driver.get("https://www.google.com")
        search_box = driver.find_element_by_name("q")
        search_box.send_keys(search_query)
        search_box.send_keys(Keys.RETURN)
        search_results = driver.find_elements_by_css_selector(".g")
        driver.quit()
    return render_template('web_browsing.html', title='Web Browsing', search_results=search_results)

if __name__ == '__main__':
    app.run(debug=True)