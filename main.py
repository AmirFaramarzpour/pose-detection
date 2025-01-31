import cv2
import mediapipe as mp
import time
import requests
import customtkinter as ctk
from tkinter import messagebox
import pyttsx3
import json
import os
from PIL import Image, ImageTk

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose(min_detection_confidence=0.7, min_tracking_confidence=0.7)

# Save credentials to a file
def save_credentials():
    credentials = {
        "bot_token": bot_token_var.get(),
        "chat_id": chat_id_var.get()
    }
    with open("credentials.json", "w") as file:
        json.dump(credentials, file)
    messagebox.showinfo("Credentials Saved", "Your credentials have been saved successfully.")

# Load credentials from a file
def load_credentials():
    if os.path.exists("credentials.json"):
        with open("credentials.json", "r") as file:
            credentials = json.load(file)
        return credentials["bot_token"], credentials["chat_id"]
    return "", ""

# Telegram notification function
def send_telegram_notification(message):
    bot_token = bot_token_var.get()
    chat_id = chat_id_var.get()
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        print(f"Failed to send notification: {response.text}")
    return response

# Voice alert function
def voice_alert(message):
    engine = pyttsx3.init()
    engine.say(message)
    engine.runAndWait()

# Stop detection
stop_detection_flag = False
cap = None

def start_detection():
    global stop_detection_flag, cap
    stop_detection_flag = False
    save_screenshot = save_screenshot_var.get()
    use_voice_alert = voice_alert_var.get()

    if cap is None or not cap.isOpened():
        cap = cv2.VideoCapture(0)
    
    def process_frame():
        if stop_detection_flag:
            return

        ret, frame = cap.read()
        if not ret:
            root.after(10, process_frame)
            return

        # Convert the BGR frame to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process the frame for pose detection
        results = pose.process(frame_rgb)

        # Draw the pose landmarks on the frame
        if results.pose_landmarks:
            # Draw landmarks
            mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            
            # Capture screenshot if enabled
            if save_screenshot:
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                filename = f"screenshot_{timestamp}.png"
                cv2.imwrite(filename, frame)
            
            # Send Telegram notification
            send_telegram_notification("Human detected: screenshot saved!")
            
            # Voice alert if enabled
            if use_voice_alert:
                voice_alert("Human detected!")

        # Display the frame in the UI
        img = Image.fromarray(frame)
        imgtk = ImageTk.PhotoImage(image=img)
        canvas.create_image(0, 0, anchor='nw', image=imgtk)
        canvas.imgtk = imgtk

        root.after(10, process_frame)

    process_frame()

def stop_detection():
    global stop_detection_flag, cap
    stop_detection_flag = True
    if cap is not None and cap.isOpened():
        cap.release()
    canvas.delete("all")

# GUI setup
def run_gui():
    global bot_token_var, chat_id_var, save_screenshot_var, voice_alert_var, start_stop_var, canvas, root, remember_me_var

    root = ctk.CTk()
    root.title("Pose Detection Settings")

    # Canvas for video display
    canvas = ctk.CTkCanvas(root, width=640, height=480)
    canvas.grid(row=0, column=0, columnspan=3, pady=10)

    ctk.CTkLabel(root, text="Telegram Bot Token:").grid(row=1, column=0, padx=10, pady=5)
    bot_token_var = ctk.StringVar()
    ctk.CTkEntry(root, textvariable=bot_token_var, width=300).grid(row=1, column=1, columnspan=2, padx=10, pady=5)

    ctk.CTkLabel(root, text="Telegram Chat ID:").grid(row=2, column=0, padx=10, pady=5)
    chat_id_var = ctk.StringVar()
    ctk.CTkEntry(root, textvariable=chat_id_var, width=300).grid(row=2, column=1, columnspan=2, padx=10, pady=5)

    save_screenshot_var = ctk.BooleanVar()
    save_screenshot_switch = ctk.CTkSwitch(root, text="Save Screenshots", variable=save_screenshot_var)
    save_screenshot_switch.grid(row=3, column=0, padx=5, pady=5)

    voice_alert_var = ctk.BooleanVar()
    voice_alert_switch = ctk.CTkSwitch(root, text="Voice Alerts", variable=voice_alert_var)
    voice_alert_switch.grid(row=3, column=1, padx=5, pady=5)

    start_stop_var = ctk.BooleanVar()
    start_stop_switch = ctk.CTkSwitch(root, text="Start/Stop Detection", variable=start_stop_var, command=lambda: start_detection() if start_stop_var.get() else stop_detection())
    start_stop_switch.grid(row=3, column=2, padx=5, pady=5)

    remember_me_var = ctk.BooleanVar()
    remember_me_check = ctk.CTkCheckBox(root, text="Remember Me", variable=remember_me_var, command=lambda: save_credentials() if remember_me_var.get() else None)
    remember_me_check.grid(row=4, column=0, columnspan=3, pady=5)

    # Load saved credentials on startup
    bot_token, chat_id = load_credentials()
    bot_token_var.set(bot_token)
    chat_id_var.set(chat_id)

    root.mainloop()

run_gui()
