import tkinter as tk
from tkinter import ttk
from tkinter import simpledialog
import cv2
from PIL import Image, ImageTk
import google.generativeai as genai
import threading


# Adjust the denisty, these values are just the first results of the density of ingredients.
DENSITY_DB = {
    'Flour': 0.59,
    'Powdered Sugar': 1.59,
    'Salt': 2.17,
    'Baking Powder': 2.2
}

# Replace "YOUR_API_KEY_HERE" with your Gemini API Key.
genai.configure(api_key="YOUR_API_KEY_HERE")

class NutritionConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Baking Converter")

        self.detected_info = tk.StringVar()

        self.container = tk.Frame(root)
        self.container.pack(side="top", fill="both", expand=True)

        self.frames = {}
        for F in (GeminiScreen, ConversionScreen):
            frame = F(self.container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(GeminiScreen)

        nav_frame = tk.Frame(root)
        nav_frame.pack(side="bottom", pady=10)

        gemini_btn = tk.Button(nav_frame, text="Camera", command=lambda: self.show_frame(GeminiScreen))
        conv_btn = tk.Button(nav_frame, text="Converter", command=lambda: self.show_frame(ConversionScreen))
        gemini_btn.pack(side="left", padx=10)
        conv_btn.pack(side="left", padx=10)

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

class GeminiScreen(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        self.canvas = tk.Canvas(self, width=640, height=480)
        self.canvas.pack()

        self.image_on_canvas = self.canvas.create_image(0, 0, anchor=tk.NW)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)

        self.capture_btn = tk.Button(btn_frame, text="Capture Image", command=self.capture_image)
        self.capture_btn.pack(side="left", padx=10)

        self.retake_btn = tk.Button(btn_frame, text="Retake", command=self.retake_image)
        self.retake_btn.pack(side="left", padx=10)
        self.retake_btn.config(state="disabled")

        self.analyze_btn = tk.Button(btn_frame, text="Analyze", command=self.analyze_with_gemini)
        self.analyze_btn.pack(side="left", padx=10)

        self.result_label = tk.Label(btn_frame, textvariable=controller.detected_info, wraplength=600, justify="left")
        self.result_label.pack(side="left", padx=10)

        self.captured_image = None
        self.latest_frame = None
        self.streaming = False
        self.frame_skip = 3
        self.gui_frame_counter = 0

        self.ask_for_ip_port()

        self.start_video_thread()
        self.update_video_gui()

    def ask_for_ip_port(self):
        ip = simpledialog.askstring("Camera IP", "Enter the IP address:")
        port = simpledialog.askstring("Camera Port", "Enter the port:")

        stream_url = f"http://{ip}:{port}/video" if ip and port else 0
        self.video_stream = cv2.VideoCapture(stream_url)

    def start_video_thread(self):
        self.streaming = True
        self.capture_thread = threading.Thread(target=self.capture_frames, daemon=True)
        self.capture_thread.start()

    def capture_frames(self):
        while self.streaming:
            ret, frame = self.video_stream.read()
            if ret:
                self.latest_frame = frame

    def update_video_gui(self):
        if self.streaming and self.latest_frame is not None:
            self.gui_frame_counter += 1
            if self.gui_frame_counter % self.frame_skip == 0:
                frame_rgb = cv2.cvtColor(self.latest_frame, cv2.COLOR_BGR2RGB)
                self.photo = ImageTk.PhotoImage(image=Image.fromarray(frame_rgb))
                self.canvas.itemconfig(self.image_on_canvas, image=self.photo)
        self.after(30, self.update_video_gui)

    def capture_image(self):
        if self.latest_frame is not None:
            self.streaming = False
            self.captured_image = self.latest_frame.copy()

            cv2.imwrite("captured_ingredient.jpg", self.captured_image)

            frame_rgb = cv2.cvtColor(self.captured_image, cv2.COLOR_BGR2RGB)
            self.photo = ImageTk.PhotoImage(image=Image.fromarray(frame_rgb))
            self.canvas.itemconfig(self.image_on_canvas, image=self.photo)

            self.controller.detected_info.set("Image captured.")
            self.retake_btn.config(state="normal")

    def retake_image(self):
        self.streaming = True
        self.start_video_thread()
        self.retake_btn.config(state="disabled")
        self.controller.detected_info.set("Resumed video stream.")

    def analyze_with_gemini(self):
        if self.captured_image is None:
            self.controller.detected_info.set("Please capture an image first.")
            return

        _, jpeg_data = cv2.imencode('.jpg', self.captured_image)
        image_bytes = jpeg_data.tobytes()

        model = genai.GenerativeModel('gemini-1.5-flash')
        try:
            response = model.generate_content(
                contents=[
                    {
                        "parts": [
                            {"mime_type": "image/jpeg", "data": image_bytes},
                            {"text": "You have 4 choices, 'Flour', 'Powdered Sugar', 'Salt', 'Baking Powder'. What ingredient is shown in this image? Answer with only the name of the ingredient, and predict the density of the ingredient in grams per milliliter."}
                        ]
                    }
                ]
            )
            self.controller.detected_info.set(response.text)
        except Exception as e:
            self.controller.detected_info.set(f"Error: {str(e)}")

    def destroy(self):
        self.streaming = False
        self.video_stream.release()
        super().destroy()

class ConversionScreen(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        form_frame = tk.Frame(self)
        form_frame.pack(pady=20)

        tk.Label(form_frame, text="Amount:").grid(row=0, column=0, padx=5, pady=5)
        self.amount = tk.Entry(form_frame)
        self.amount.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(form_frame, text="Unit:").grid(row=1, column=0, padx=5, pady=5)
        self.unit = ttk.Combobox(form_frame, values=['Cups', 'Tablespoons', 'Teaspoons'])
        self.unit.grid(row=1, column=1, padx=5, pady=5)
    
        tk.Label(form_frame, text="of Ingredient:").grid(row=2, column=0, padx=5, pady=5)
        self.ingredient = ttk.Combobox(form_frame, values=list(DENSITY_DB.keys()))
        self.ingredient.grid(row=2, column=1, padx=5, pady=5)

        convert_btn = tk.Button(form_frame, text="Convert", command=self.convert)
        convert_btn.grid(row=3, columnspan=2, pady=10)

        self.result = tk.Label(self, text="")
        self.result.pack(pady=10)

    def convert(self):
        try:
            ingredient = self.ingredient.get()
            amount = float(self.amount.get())
            unit = self.unit.get()

            unit_ml = {
                'Cups': 250,
                'Tablespoons': 14,
                'Teaspoons': 5
            }.get(unit, 1)

            if ingredient in DENSITY_DB:
                grams = amount * unit_ml * DENSITY_DB[ingredient]
                self.result.config(text=f"{amount} {unit} = {grams:.1f} grams")
            else:
                self.result.config(text="Ingredient not found in database")
        except ValueError:
            self.result.config(text="Please enter a valid numeric amount.")

if __name__ == "__main__":
    root = tk.Tk()
    app = NutritionConverter(root)
    root.mainloop()
