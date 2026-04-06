from flask import Flask, render_template, request
import base64
import requests
import re
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Merr API key nga Environment Variable (vendos në Render)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

def analyze_food_base64(data_url):
    try:
        img_str = re.search(r'base64,(.*)', data_url).group(1)
        image_bytes = base64.b64decode(img_str)

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'camera_food.jpg')
        with open(filepath, 'wb') as f:
            f.write(image_bytes)

        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
        json_data = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Identify this food and estimate calories (short answer)."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_str}"}}
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
            result = analyze_food_base64(
                f"data:image/jpeg;base64,{base64.b64encode(open(filepath,'rb').read()).decode()}"
            )

    # Ngarkim nga kamera (opsional)
    elif request.method == "POST" and "food_image_camera" in request.form:
        data_url = request.form.get("food_image_camera")
        if data_url:
            result = analyze_food_base64(data_url)

    return render_template("index.html", result=result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)