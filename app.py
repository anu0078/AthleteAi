import os
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

# ── App setup ──────────────────────────────────────────────────────────────────

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
ALLOWED_EXT   = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'athleteai-dev-secret-2024')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

from database   import Database
from ai_service import AIService

db = Database()
ai = AIService()


# ── Helpers ────────────────────────────────────────────────────────────────────

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT


# ── Page routes ────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# ── API: Users ─────────────────────────────────────────────────────────────────

@app.route('/api/user', methods=['POST'])
def create_user():
    try:
        name          = request.form.get('name', '').strip()
        age           = request.form.get('age', '18')
        sport         = request.form.get('sport', 'athletics')
        fitness_level = request.form.get('fitness_level', 'beginner')
        language      = request.form.get('language', 'en')
        city          = request.form.get('city', '')
        weight        = request.form.get('weight', '')
        height        = request.form.get('height', '')
        gender        = request.form.get('gender', 'male')

        if not name:
            return jsonify({'success': False, 'error': 'Name is required'}), 400

        try:
            age = int(age)
        except (ValueError, TypeError):
            age = 18

        photo_path = None
        photo = request.files.get('photo')
        if photo and photo.filename and allowed_file(photo.filename):
            ts       = int(datetime.now().timestamp())
            filename = secure_filename(f"{ts}_{photo.filename}")
            save_to  = os.path.join(UPLOAD_FOLDER, filename)
            photo.save(save_to)
            photo_path = save_to

        user_id = db.create_user(
            name=name, age=age, sport=sport, fitness_level=fitness_level,
            language=language, city=city, weight=weight, height=height,
            gender=gender, photo_path=photo_path
        )

        return jsonify({'success': True, 'user_id': user_id})

    except Exception as exc:
        print(f"[create_user] {exc}")
        return jsonify({'success': False, 'error': str(exc)}), 500


@app.route('/api/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        user = db.get_user(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Don't expose raw filesystem path to frontend
        if user.get('photo_path'):
            user['has_photo'] = True
            del user['photo_path']

        plan = db.get_latest_plan(user_id)
        return jsonify({'success': True, 'user': user, 'plan': plan})

    except Exception as exc:
        print(f"[get_user] {exc}")
        return jsonify({'success': False, 'error': str(exc)}), 500


# ── API: Plans ─────────────────────────────────────────────────────────────────

@app.route('/api/generate-plan', methods=['POST'])
def generate_plan():
    try:
        data    = request.get_json(silent=True) or {}
        user_id = data.get('user_id')

        if not user_id:
            return jsonify({'success': False, 'error': 'user_id required'}), 400

        user = db.get_user(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        workout_plan   = ai.generate_workout_plan(user)
        nutrition_plan = ai.generate_nutrition_plan(user)
        plan_id        = db.save_plan(user_id, workout_plan, nutrition_plan)

        return jsonify({
            'success':        True,
            'plan_id':        plan_id,
            'workout_plan':   workout_plan,
            'nutrition_plan': nutrition_plan,
        })

    except Exception as exc:
        print(f"[generate_plan] {exc}")
        return jsonify({'success': False, 'error': str(exc)}), 500


# ── API: Photo analysis ────────────────────────────────────────────────────────

@app.route('/api/analyze-photo', methods=['POST'])
def analyze_photo():
    try:
        user_id = request.form.get('user_id')
        photo   = request.files.get('photo')

        if not photo or not photo.filename:
            return jsonify({'success': False, 'error': 'No photo provided'}), 400
        if not allowed_file(photo.filename):
            return jsonify({'success': False, 'error': 'Unsupported file type'}), 400

        user         = db.get_user(user_id) if user_id else None
        photo_bytes  = photo.read()
        content_type = photo.content_type or 'image/jpeg'
        analysis     = ai.analyze_photo(photo_bytes, content_type, user)

        return jsonify({'success': True, 'analysis': analysis})

    except Exception as exc:
        print(f"[analyze_photo] {exc}")
        return jsonify({'success': False, 'error': str(exc)}), 500


# ── API: Progress ──────────────────────────────────────────────────────────────

@app.route('/api/progress', methods=['POST'])
def log_progress():
    try:
        data    = request.get_json(silent=True) or {}
        user_id = data.get('user_id')

        if not user_id:
            return jsonify({'success': False, 'error': 'user_id required'}), 400

        progress_id = db.log_progress(
            user_id      = int(user_id),
            completed    = data.get('completed', False),
            notes        = data.get('notes', ''),
            weight       = data.get('weight'),
            energy_level = data.get('energy_level', 5),
        )

        return jsonify({'success': True, 'progress_id': progress_id})

    except Exception as exc:
        print(f"[log_progress] {exc}")
        return jsonify({'success': False, 'error': str(exc)}), 500


@app.route('/api/progress/<int:user_id>', methods=['GET'])
def get_progress(user_id):
    try:
        progress = db.get_progress(user_id)
        streak   = db.get_streak(user_id)
        return jsonify({'success': True, 'progress': progress, 'streak': streak})

    except Exception as exc:
        print(f"[get_progress] {exc}")
        return jsonify({'success': False, 'error': str(exc)}), 500


# ── Run ────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    port  = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    print(f"\n🏆 AthleteAI starting on http://localhost:{port}\n")
    app.run(host='0.0.0.0', port=port, debug=debug)
