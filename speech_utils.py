import pyttsx3

engine = pyttsx3.init()


def speak_question(text):
    engine.say(text)
    engine.runAndWait()