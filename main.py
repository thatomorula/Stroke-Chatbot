from flask import Flask, render_template, request
import pandas as pd
from joblib import load
from sklearn.preprocessing import LabelEncoder
from flask import Flask, render_template, request, jsonify
from flask import Flask, render_template, request, redirect, url_for
import openai
from flask import session

openai.api_key = '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'

def categorize_age(value):
    if value <= 20:
        return 0
    elif value <= 40:
        return 1
    elif value <= 60:
        return 2
    elif value <= 80:
        return 3
    else:
        return 4

def categorize_bmi(value):
    if value <= 18.5:
        return 5
    elif value <= 24.5:
        return 0
    elif value <= 29.9:
        return 3
    elif value <= 34.9:
        return 1
    elif value <= 39.9:
        return 2
    else:
        return 4

def categorize_avg_glucose(value):
    if value < 70:
        return 1
    elif value <= 99:
        return 2
    elif value <= 125:
        return 4
    else:
        return 0

def encode_hypertension(value):
    mapping = {'No': 0, 'Yes': 1}
    return mapping.get(value, -1)

def encode_heart_disease(value):
    mapping = {'No': 0, 'Yes': 1}
    return mapping.get(value, -1)

def encode_ever_married(value):
    mapping = {'No': 0, 'Yes': 1}
    return mapping.get(value, -1)

def encode_work_type(value):
    work_categories = {
        "Private": 0,
        "Self-employed": 1,
        "Govt_job": 2,
        "children": 3,
        "Never_worked": 4
    }
    return work_categories.get(value, -1)

def encode_residence(value):
    return 1 if value == "Urban" else 0

def encode_smoking_status(value):
    smoking_categories = {
        "formerly smoked": 1,
        "never smoked": 2,
        "smokes": 3,
        "unknown": 0
    }
    return smoking_categories.get(value, -1)

def encode_gender(value):
    gender_mapping = {
        'Male': 0,
        'Female': 1,
    }
    return gender_mapping.get(value, -1)  # returning -1 for unexpected values

# age 20, glu 129, bmi 100
doctors_diagonis = None
doctors_recommendation = None
doctors_medication_prescribed = None

app = Flask(__name__)

app.secret_key = '8c6f76d69d4935d5bebf282133a18b9d'

@app.route('/')
def home():
    return render_template('chatbot.html')

@app.route('/predict', methods=['GET', 'POST'])
def predict_stroke():
    # Load the model from the file
    lr_model = load('logistic_regression_model.joblib')

    prediction = None
    interpretation = ""
    if request.method == 'POST':
        # Extract data from form
        data = {
            'gender': [encode_gender(request.form.get('gender'))],
            'age': [categorize_age(int(request.form.get('age')))],  # Convert age to float
            'ever_married': [encode_ever_married(request.form.get('ever_married'))],
            'work_type': [encode_work_type(request.form.get('work_type'))],
            'Residence_type': [encode_residence(request.form.get('Residence_type'))],
            'hypertension': [encode_hypertension(request.form.get('hypertension'))],
            'heart_disease': [encode_heart_disease(request.form.get('heart_disease'))],
            'avg_glucose_level': [categorize_avg_glucose(float(request.form.get('avg_glucose_level')))],
            # Convert to float
            'bmi': [categorize_bmi(float(request.form.get('bmi')))],  # Convert to float
            'smoking_status': [encode_smoking_status(request.form.get('smoking_status'))]
        }

        # Convert data into DataFrame
        data = pd.DataFrame(data)

        columns = ['ever_married', 'hypertension', 'heart_disease', 'age_0', 'age_1',
                   'age_2', 'age_3', 'age_4', 'avg_glucose_level_0', 'avg_glucose_level_1',
                   'avg_glucose_level_2', 'avg_glucose_level_3', 'bmi_0', 'bmi_1', 'bmi_2',
                   'bmi_3', 'bmi_4', 'bmi_5', 'gender_0', 'gender_1', 'work_type_0',
                   'work_type_1', 'work_type_2', 'work_type_3', 'work_type_4',
                   'Residence_type_0', 'Residence_type_1', 'smoking_status_0',
                   'smoking_status_1', 'smoking_status_2', 'smoking_status_3']

        # One-hot encode categorical features
        categorical_features = ['age', 'avg_glucose_level', 'bmi', 'gender', 'work_type', 'Residence_type',
                                'smoking_status']
        data = pd.get_dummies(data, columns=categorical_features)

        for feature in columns:
            if feature not in data.columns:
                data[feature] = 0

        data = data[columns]
        data = data.astype('float32')

        # Use your model to predict
        prediction = str(int(lr_model.predict(data)))

    return render_template('predict.html', prediction=prediction, interpretation=interpretation,text_color="white")

@app.route('/chatbot', methods=['GET','POST'])
def chat():
    if request.method == 'POST':
        # Handle POST request
        user_input = request.json['message']
        #messages = [{"role": "system", "content": "You are a helpful stroke assistant."}]
        diagnosis = session.get('diagnosis', '8c6f76d69d4935d5bebf282133a18b9d')
        medications = session.get('medications', '8c6f76d69d4935d5bebf282133a18b9d')
        recommendations = session.get('recommendations', '8c6f76d69d4935d5bebf282133a18b9d')
        doctor_note_content = f"Doctor's Note - Diagnosis: {diagnosis}, Medications: {medications}, Recommendations: {recommendations}"


        messages = [
            {"role": "system", "content": "You are StrokeGPT, a virtual health assistant designed to provide guidance, answer questions, and assist patients in understanding and managing their stroke-related health conditions. With the ability to understand and respond to users based on the doctor's note which includes diagonsis, medication prescribed and recommendations. You can also interpret real-time stroke predictions results given to you for the user, explain the significance of the results, and analyze individual factors contributing to their health status. For instance, if the stroke prediction is negative but the user exhibits high average glucose levels or hypertension, you can pinpoint these concerns, offer preliminary suggestions, and strongly recommend consultation with a healthcare professional. You prioritize empathy, and clarity in all interactions.Make sue to keep the words in the limit of 200 words"},
            {"role": "system", "content": doctor_note_content}
        ]

        messages.append({"role": "user", "content": user_input})
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=200
        )
        assistant_message = response.choices[0].message['content']
        return jsonify({"message": assistant_message})
    else:
        # Handle GET request
        # Return a view or some information
        return render_template('chatbot.html')

@app.route('/doctor_note', methods=['GET','POST'])
def doctor_note():

    if request.method == 'POST':
        session['diagnosis'] = request.form.get('diagnosis')
        session['medications'] = request.form.get('medications')
        session['recommendations'] = request.form.get('recommendations')

    diagnosis = session.get('diagnosis', '8c6f76d69d4935d5bebf282133a18b9d')
    medications = session.get('medications', '8c6f76d69d4935d5bebf282133a18b9d')
    recommendations = session.get('recommendations', '8c6f76d69d4935d5bebf282133a18b9d')

    return render_template('doctor_note.html', diagnosis=diagnosis, medications=medications,
                           recommendations=recommendations, text_color="white")

#if __name__ == '__main__':
#    app.run(debug=True)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
