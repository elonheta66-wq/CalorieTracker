from flask import Flask, render_template, request, url_for
import base64
import requests
import re
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Merr API key nga Environment Variable (vendos në Render)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

def analyze_food(image_filename):
    try:
        # Krijo URL publike për foton
        image_url = url_for('static', filename=f'uploads/{image_filename}', _external=True)
        
        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
        json_data = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Identify this food and estimate its calories. Answer shortly in format: Food name – Calories kcal."},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }
            ]
        }

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=json_data
        )

        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print("Error:", e)
        return "Gabim: nuk mund të analizoj foton"

@app.route("/", methods=["GET", "POST"])
def home():
    result = None

    # Ngarkim nga kompjuteri
    if request.method == "POST" and "food_image" in request.files:
        image = request.files["food_image"]
        if image:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
            image.save(filepath)
            result = analyze_food(image.filename)

    # Ngarkim nga kamera (opsional)
    elif request.method == "POST" and "food_image_camera" in request.form:
        data_url = request.form.get("food_image_camera")
        if data_url:
            # Ruaj foton nga kamera
            img_str = re.search(r'base64,(.*)', data_url).group(1)
            image_bytes = base64.b64decode(img_str)
            filename = "camera_food.jpg"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            with open(filepath, 'wb') as f:
                f.write(image_bytes)
            result = analyze_food(filename)

    return render_template("index.html", result=result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)