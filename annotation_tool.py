import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import json


class AnnotationTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Annotation Tool")
        self.canvas = tk.Canvas(root, width=800, height=600)
        self.canvas.pack()

        # Initialize the image and annotations list
        self.img = None
        self.annotations = {}
        self.rect = None
        self.start_x = None
        self.start_y = None

        # Buttons and entries for control
        btn_load = tk.Button(root, text="Load Image", command=self.load_image)
        btn_load.pack(side=tk.LEFT)

        btn_save = tk.Button(root, text="Save Annotations",
                             command=self.save_annotations)
        btn_save.pack(side=tk.LEFT)

        self.label_entry = tk.Entry(root)
        self.label_entry.pack(side=tk.LEFT)
        self.label_entry.bind("<Return>", self.add_label)  # Bind the Enter key

        btn_label = tk.Button(root, text="Add Label", command=self.add_label)
        btn_label.pack(side=tk.LEFT)

        # Bind mouse events
        self.canvas.bind("<ButtonPress-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        # Adjust focus on release after dragging
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

    def load_image(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.img = Image.open(file_path)
            self.tk_img = ImageTk.PhotoImage(self.img)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_img)

    def on_click(self, event):
        # Start drawing the rectangle
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y, outline='red')

    def on_drag(self, event):
        # Update the rectangle as we drag the mouse
        self.canvas.coords(self.rect, self.start_x,
                           self.start_y, event.x, event.y)

    def on_release(self, event):
        # After releasing the mouse, focus the label entry if a rectangle was actually drawn
        coords = self.canvas.coords(self.rect)
        # Check for non-trivial size
        if self.rect and (coords[2] - coords[0] > 1 or coords[3] - coords[1] > 1):
            self.label_entry.focus_set()

    def add_label(self, event=None):  # Optional event argument for the key bind
        label = self.label_entry.get().strip()
        if label:  # Check if the label is not empty
            coords = self.canvas.coords(self.rect)
            self.annotations[self.rect] = {
                'label': label, 'coordinates': coords}
            # Display the label on the canvas
            x1, y1, _, _ = coords
            self.canvas.create_text(
                x1, y1, anchor='nw', text=label, font=("Purisa", 10), fill="blue")
            self.label_entry.delete(0, tk.END)
            # Remove focus from the entry field
            self.canvas.focus_set()  # Set focus back to the canvas or some other neutral place

    def save_annotations(self):
        # Save the annotations to a JSON file
        with open("annotations.json", "w") as file:
            json.dump(self.annotations, file, indent=4)
        print("Annotations saved!")


if __name__ == "__main__":
    root = tk.Tk()
    app = AnnotationTool(root)
    root.mainloop()
