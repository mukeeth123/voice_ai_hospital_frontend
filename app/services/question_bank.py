
# Question Bank for Arogya AI Intake
# Keys end with _self or _other to handle "Your" vs "Patient's" phrasing.

QUESTION_BANK = {
    "patient_relation": {
        "English": "Hello! Welcome to Amrutha.AI. I am Virtual Patient Onboarding Receptionist.Who is this appointment for? (Yourself, Parents, Child, Friend)",
        "Hindi": "नमस्ते!Amrutha.AI में आपका स्वागत है.मैं वर्चुअल पेशेंट ऑनबोर्डिंग रिसेप्शनिस्ट हूँ।.यह अपॉइंटमेंट किसके लिए है? (आप खुद, माता-पिता, बच्चे, या दोस्त)",
        "Kannada": "ನಮಸ್ಕಾರ! ಅಮೃತ.ಎಐ ಗೆ ಸುಸ್ವಾಗತ.ನಾನು ವರ್ಚುವಲ್ ರೋಗಿಯ ಆನ್‌ಬೋರ್ಡಿಂಗ್ ಸ್ವಾಗತಕಾರ.. ಈ ಅಪಾಯಿಂಟ್‌ಮೆಂಟ್ ಯಾರಿಗಾಗಿ? (ನೀವು, ಪೋಷಕರು, ಮಕ್ಕಳು, ಸ್ನೇಹಿತರು)"
    },
    
    # --- NAME ---
    "name_self": {
        "English": "Could you please tell me your full name?",
        "Hindi": "कृपया अपना पूरा नाम बताएं?",
        "Kannada": "ದಯವಿಟ್ಟು ನಿಮ್ಮ ಪೂರ್ಣ ಹೆಸರನ್ನು ಹೇಳಿ?"
    },
    "name_other": {
        "English": "Could you please tell me the patient's full name?",
        "Hindi": "कृपया मरीज का पूरा नाम बताएं?",
        "Kannada": "ದಯವಿಟ್ಟು ರೋಗಿಯ ಪೂರ್ಣ ಹೆಸರನ್ನು ಹೇಳಿ?"
    },

    # --- AGE ---
    "age_self": {
        "English": "Thanks {name}. How old are you?",
        "Hindi": "धन्यवाद {name}. आपकी उम्र क्या है?",
        "Kannada": "ಧನ್ಯವಾದಗಳು {name}. ನಿಮ್ಮ ವಯಸ್ಸು ಎಷ್ಟು?"
    },
    "age_other": {
        "English": "Thanks. How old is {name}?",
        "Hindi": "धन्यवाद। {name} की उम्र क्या है?",
        "Kannada": "ಧನ್ಯವಾದಗಳು. {name} ಅವರ ವಯಸ್ಸು ಎಷ್ಟು?"
    },

    # --- GENDER ---
    "gender_self": {
        "English": "What is your gender? (Male, Female, Other)",
        "Hindi": "आपका लिंग क्या है? (पुरुष, महिला, अन्य)",
        "Kannada": "ನಿಮ್ಮ ಲಿಂಗ ಯಾವುದು? (ಗಂಡು, ಹೆಣ್ಣು, ಇತರೆ)"
    },
    "gender_other": {
        "English": "What is the patient's gender? (Male, Female, Other)",
        "Hindi": "मरीज का लिंग क्या है? (पुरुष, महिला, अन्य)",
        "Kannada": "ರೋಗಿಯ ಲಿಂಗ ಯಾವುದು? (ಗಂಡು, ಹೆಣ್ಣು, ಇತರೆ)"
    },

    # --- PHONE ---
    "phone": { 
        "English": "Please share your 10-digit phone number.",
        "Hindi": "कृपया अपना 10 अंकों का फोन नंबर साझा करें।",
        "Kannada": "ದಯವಿಟ್ಟು ನಿಮ್ಮ 10 ಅಂಕಿಗಳ ಫೋನ್ ಸಂಖ್ಯೆಯನ್ನು ಹಂಚಿಕೊಳ್ಳಿ."
    },

    # --- EMAIL ---
    "email": { 
        "English": "Please provide your email address. We will send the report here.",
        "Hindi": "कृपया अपना ईमेल पता दें। हम रिपोर्ट यहीं भेजेंगे।",
        "Kannada": "ದಯವಿಟ್ಟು ನಿಮ್ಮ ಇಮೇಲ್ ವಿಳಾಸವನ್ನು ನೀಡಿ. ನಾವು ವರದಿಯನ್ನು ಇಲ್ಲಿಗೆ ಕಳುಹಿಸುತ್ತೇವೆ."
    },

    # --- LOCATION ---
    "location": {
        "English": "Where are you currently located (City)?",
        "Hindi": "आप वर्तमान में कहाँ स्थित हैं (शहर)?",
        "Kannada": "ನೀವು ಪ್ರಸ್ತುತ ಎಲ್ಲಿದ್ದೀರಿ (ನಗರ)?"
    },

    # --- WEIGHT ---
    "weight_self": {
        "English": "What is your approximate weight (in kg)?",
        "Hindi": "आपका अनुमानित वजन (किलो में) क्या है?",
        "Kannada": "ನಿಮ್ಮ ಅಂದಾಜು ತೂಕ (ಕೆಜಿಗಳಲ್ಲಿ) ಎಷ್ಟು?"
    },
    "weight_other": {
        "English": "What is {name}'s approximate weight (in kg)?",
        "Hindi": "{name} का अनुमानित वजन (किलो में) क्या है?",
        "Kannada": "{name} ಅವರ ಅಂದಾಜು ತೂಕ (ಕೆಜಿಗಳಲ್ಲಿ) ಎಷ್ಟು?"
    },

    # --- BLOOD GROUP ---
    "blood_group_self": {
        "English": "What is your Blood Group? (e.g. A+, O-, Don't Know)",
        "Hindi": "आपका ब्लड ग्रुप क्या है? (जैसे A+, O-, पता नहीं)",
        "Kannada": "ನಿಮ್ಮ ರಕ್ತದ ಗುಂಪು ಯಾವುದು? (ಉದಾಹರಣೆಗೆ A+, O-, ಗೊತ್ತಿಲ್ಲ)"
    },
    "blood_group_other": {
        "English": "What is the patient's Blood Group?",
        "Hindi": "मरीज का ब्लड ग्रुप क्या है?",
        "Kannada": "ರೋಗಿಯ ರಕ್ತದ ಗುಂಪು ಯಾವುದು?"
    },

    # --- SYMPTOMS ---
    "symptoms_self": {
        "English": "Okay {name}, could you please describe your symptoms in detail?",
        "Hindi": "ठीक है {name}, कृपया अपने लक्षणों का विस्तार से वर्णन करें?",
        "Kannada": "ಸರಿ {name}, ದಯವಿಟ್ಟು ನಿಮ್ಮ ರೋಗಲಕ್ಷಣಗಳನ್ನು ವಿವರವಾಗಿ ವಿವರಿಸಿ?"
    },
    "symptoms_other": {
        "English": "Okay, could you please describe {name}'s symptoms in detail?",
        "Hindi": "ठीक है, कृपया {name} के लक्षणों का विस्तार से वर्णन करें?",
        "Kannada": "ಸರಿ, ದಯವಿಟ್ಟು {name} ಅವರ ರೋಗಲಕ್ಷಣಗಳನ್ನು ವಿವರವಾಗಿ ವಿವರಿಸಿ?"
    },

    # --- DURATION ---
    "duration": { 
        "English": "For how many days have these symptoms been present?",
        "Hindi": "ये लक्षण कितने दिनों से हैं?",
        "Kannada": "ಈ ರೋಗಲಕ್ಷಣಗಳು ಎಷ್ಟು ದಿನಗಳಿಂದ ಇವೆ?"
    },

    # --- HISTORY ---
    "bp_history_self": {
        "English": "Do you have High Blood Pressure (BP)?",
        "Hindi": "क्या आपको हाई ब्लड प्रेशर (BP) की समस्या है?",
        "Kannada": "ನಿಮಗೆ ರಕ್ತದೊತ್ತಡ (BP) ಇದೆಯೇ?"
    },
    "bp_history_other": {
        "English": "Does the patient have High Blood Pressure (BP)?",
        "Hindi": "क्या मरीज को हाई ब्लड प्रेशर (BP) की समस्या है?",
        "Kannada": "ರೋಗಿಗೆ ರಕ್ತದೊತ್ತಡ (BP) ಇದೆಯೇ?"
    },

    "sugar_history_self": {
        "English": "Do you have Diabetes (Sugar)?",
        "Hindi": "क्या आपको शुगर (Diabetes) की बीमारी है?",
        "Kannada": "ನಿಮಗೆ ಸಕ್ಕರೆ ಕಾಯಿಲೆ (Diabetes) ಇದೆಯೇ?"
    },
    "sugar_history_other": {
        "English": "Does the patient have Diabetes (Sugar)?",
        "Hindi": "क्या मरीज को शुगर (Diabetes) की बीमारी है?",
        "Kannada": "ರೋಗಿಗೆ ಸಕ್ಕರೆ ಕಾಯಿಲೆ (Diabetes) ಇದೆಯೇ?"
    },

    "thyroid_history_self": {
        "English": "Do you have any Thyroid issues?",
        "Hindi": "क्या आपको थायराइड की समस्या है?",
        "Kannada": "ನಿಮಗೆ ಥೈರಾಯ್ಡ್ ಸಮಸ್ಯೆ ಇದೆಯೇ?"
    },
    "thyroid_history_other": {
        "English": "Does the patient have any Thyroid issues?",
        "Hindi": "क्या मरीज को थायराइड की समस्या है?",
        "Kannada": "ರೋಗಿಗೆ ಥೈರಾಯ್ಡ್ ಸಮಸ್ಯೆ ಇದೆಯೇ?"
    },

    "surgeries_self": {
        "English": "Have you had any past surgeries?",
        "Hindi": "क्या आपकी पहले कोई सर्जरी हुई है?",
        "Kannada": "ನಿಮಗೆ ಹಿಂದೆ ಯಾವುದಾದರೂ ಶಸ್ತ್ರಚಿಕಿತ್ಸೆ ಆಗಿದೆಯೇ?"
    },
    "surgeries_other": {
        "English": "Has the patient had any past surgeries?",
        "Hindi": "क्या मरीज की पहले कोई सर्जरी हुई है?",
        "Kannada": "ರೋಗಿಗೆ ಹಿಂದೆ ಯಾವುದಾದರೂ ಶಸ್ತ್ರಚಿಕಿತ್ಸೆ ಆಗಿದೆಯೇ?"
    },

    "medications_self": {
        "English": "Are you currently taking any medications?",
        "Hindi": "क्या आप अभी कोई दवा ले रहे हैं?",
        "Kannada": "ನೀವು ಪ್ರಸ್ತುತ ಯಾವುದೇ ಔಷಧಿಗಳನ್ನು ತೆಗೆದುಕೊಳ್ಳುತ್ತಿದ್ದೀರಾ?"
    },
    "medications_other": {
        "English": "Is the patient currently taking any medications?",
        "Hindi": "क्या मरीज अभी कोई दवा ले रहा है?",
        "Kannada": "ರೋಗಿ ಪ್ರಸ್ತುತ ಯಾವುದೇ ಔಷಧಿಗಳನ್ನು ತೆಗೆದುಕೊಳ್ಳುತ್ತಿದ್ದಾರೆಯೇ?"
    },

    # --- DOCTOR ASSIGNMENT ---
    "assigned_doctor": {
        "English": "Based on your symptoms, I have assigned you to **{doctor_name}**. Consultation fee: ₹500. Would you like to proceed?",
        "Hindi": "आपके लक्षणों के आधार पर, मैंने आपको **{doctor_name}** के साथ नियुक्त किया है। परामर्श शुल्क: ₹500। क्या आप आगे बढ़ना चाहेंगे?",
        "Kannada": "ನಿಮ್ಮ ರೋಗಲಕ್ಷಣಗಳ ಆಧಾರದ ಮೇಲೆ, ನಾನು ನಿಮ್ಮನ್ನು **{doctor_name}** ಅವರಿಗೆ ನಿಯೋಜಿಸಿದ್ದೇನೆ. ಸಮಾಲೋಚನೆ ಶುಲ್ಕ: ₹500. ನೀವು ಮುಂದುವರಿಯಲು ಬಯಸುವಿರಾ?"
    },

    # --- SLOT SELECTION ---
    "selected_slot": {
        "English": "Please select a convenient appointment time:",
        "Hindi": "कृपया एक सुविधाजनक अपॉइंटमेंट समय चुनें:",
        "Kannada": "ದಯವಿಟ್ಟು ಅನುಕೂಲಕರ ಅಪಾಯಿಂಟ್‌ಮೆಂಟ್ ಸಮಯವನ್ನು ಆಯ್ಕೆಮಾಡಿ:"
    },

    # --- PAYMENT ---
    "payment_status": {
        "English": "Thank you {name}. Please pay ₹500 to confirm your appointment with {doctor_name}.",
        "Hindi": "धन्यवाद {name}। कृपया {doctor_name} के साथ अपनी अपॉइंटमेंट की पुष्टि करने के लिए ₹500 का भुगतान करें।",
        "Kannada": "ಧನ್ಯವಾದಗಳು {name}. {doctor_name} ಅವರೊಂದಿಗೆ ನಿಮ್ಮ ಅಪಾಯಿಂಟ್‌ಮೆಂಟ್ ಖಚಿತಪಡಿಸಲು ದಯವಿಟ್ಟು ₹500 ಪಾವತಿಸಿ."
    }
}
