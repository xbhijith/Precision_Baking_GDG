import tkinter as tk
from tkinter import ttk
import cv2
from PIL import Image, ImageTk
import numpy as np
from ultralytics import YOLO 

DENSITY_DB = {
    'Flour': 0.56,
    'Sugar': 0.85,
    'Salt': 1.20,
    'Baking Powder': 0.74
}

class IngredientDetector:
    def __init__(self, model_path='best.pt'):
        try:
            self.model = YOLO(model_path)
            self.model_loaded = True
            print("Model loaded successfully.")
        except Exception as e:
            print(f"Error loading model: {e}")
            self.model_loaded = False

    def detect_amount(self, frame):
        """
        Run inference on the frame using YOLOv8 and estimate the ingredient amount.
        For demonstration purposes, this code assumes:
          - Only one ingredient is detected per frame.
          - The detected bounding box area is used to approximate the ingredient quantity.
          - A calibration scaling factor is applied to convert pixel area to grams.
        """
        if not self.model_loaded:
            return None

        results = self.model(frame, verbose=False)
        if results and results[0].boxes is not None and len(results[0].boxes) > 0:
            box = results[0].boxes[0]
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            area = (x2 - x1) * (y2 - y1)
            scaling_factor = 0.05  # Adjust as needed, fr
            detected_amount = area * scaling_factor
            return detected_amount
        else:
            return None

class NutritionConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Baking Converter")
        
        self.vid = cv2.VideoCapture(0)
        self.current_frame = None
        self.detected_amount = tk.StringVar()
        
        self.detector = IngredientDetector(model_path='best.pt')
        
        self.container = tk.Frame(root)
        self.container.pack(side="top", fill="both", expand=True)
        
        self.frames = {}
        for F in (CameraScreen, ConversionScreen):
            frame = F(self.container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(CameraScreen)

        nav_frame = tk.Frame(root)
        nav_frame.pack(side="bottom", pady=10)
        
        cam_btn = tk.Button(nav_frame, text="Camera", 
                          command=lambda: self.show_frame(CameraScreen))
        conv_btn = tk.Button(nav_frame, text="Converter", 
                           command=lambda: self.show_frame(ConversionScreen))
        cam_btn.pack(side="left", padx=10)
        conv_btn.pack(side="left", padx=10)

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

    def release_resources(self):
        self.vid.release()

class CameraScreen(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        
        self.canvas = tk.Canvas(self, width=640, height=480)
        self.canvas.pack()
        
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)
        
        self.detect_btn = tk.Button(btn_frame, text="Detect", command=self.detect_ingredient)
        self.detect_btn.pack(side="left", padx=10)
        
        self.result_label = tk.Label(btn_frame, textvariable=controller.detected_amount)
        self.result_label.pack(side="left", padx=10)
        
        # Create the canvas image only once and update it later.
        self.image_on_canvas = self.canvas.create_image(0, 0, anchor=tk.NW)
        self.update_camera()

    def update_camera(self):
        ret, frame = self.controller.vid.read()
        if ret:
            self.controller.current_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.photo = ImageTk.PhotoImage(image=Image.fromarray(self.controller.current_frame))
            self.canvas.itemconfig(self.image_on_canvas, image=self.photo)
        self.after(10, self.update_camera)

    def detect_ingredient(self):
        if self.controller.current_frame is None:
            self.controller.detected_amount.set("No frame available")
            return
        detected_value = self.controller.detector.detect_amount(self.controller.current_frame)
        if detected_value is not None:
            self.controller.detected_amount.set(f"Detected: {detected_value:.1f}g")
        else:
            self.controller.detected_amount.set("No ingredient detected")

class ConversionScreen(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        
        form_frame = tk.Frame(self)
        form_frame.pack(pady=20)
        
        tk.Label(form_frame, text="Ingredient:").grid(row=0, column=0, padx=5, pady=5)
        self.ingredient = ttk.Combobox(form_frame, values=list(DENSITY_DB.keys()))
        self.ingredient.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(form_frame, text="Amount:").grid(row=1, column=0, padx=5, pady=5)
        self.amount = tk.Entry(form_frame)
        self.amount.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(form_frame, text="Unit:").grid(row=2, column=0, padx=5, pady=5)
        self.unit = ttk.Combobox(form_frame, values=['cups', 'tablespoons', 'teaspoons'])
        self.unit.grid(row=2, column=1, padx=5, pady=5)
        
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
                'Cups': 240,
                'Tablespoons': 15,
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
    root.protocol("WM_DELETE_WINDOW", lambda: (app.release_resources(), root.destroy()))
    root.mainloop()
    