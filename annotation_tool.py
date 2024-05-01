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
        self.currently_selected = None

        # Buttons and entries for control
        btn_load = tk.Button(root, text="Load Image", command=self.load_image)
        btn_load.pack(side=tk.LEFT)

        btn_save = tk.Button(root, text="Save Annotations",
                             command=self.save_annotations)
        btn_save.pack(side=tk.LEFT)

        self.label_entry = tk.Entry(root)
        self.label_entry.pack(side=tk.LEFT)
        self.label_entry.bind("<Return>", self.add_label)  # Bind the Enter key

        self.btn_label = tk.Button(
            root, text="Add Label", command=self.add_label, state=tk.DISABLED)  # Initially disabled
        self.btn_label.pack(side=tk.LEFT)

        # Bind mouse events
        self.canvas.bind("<ButtonPress-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

    def load_image(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.img = Image.open(file_path)
            self.tk_img = ImageTk.PhotoImage(self.img)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_img)

    def on_click(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect = None
        # Check if clicking on an existing rectangle
        for rect in self.canvas.find_withtag("rectangle"):
            x1, y1, x2, y2 = self.canvas.coords(rect)
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                if self.currently_selected:
                    self.deselect_current()
                self.currently_selected = rect
                self.canvas.itemconfig(rect, outline='green')
                self.btn_label.config(state=tk.NORMAL)
                return
        # If not clicking on a rectangle, deselect the current one
        if self.currently_selected:
            self.deselect_current()

    def on_drag(self, event):
        if not self.rect:
            self.rect = self.canvas.create_rectangle(
                self.start_x, self.start_y, event.x, event.y, outline='green', tags="rectangle")
        else:
            self.canvas.coords(self.rect, self.start_x,
                               self.start_y, event.x, event.y)

    def on_release(self, event):
        if self.rect and (self.start_x != event.x or self.start_y != event.y):
            if self.currently_selected:
                self.deselect_current()
            self.currently_selected = self.rect
            self.canvas.itemconfig(self.rect, outline='green')
            self.btn_label.config(state=tk.NORMAL)
            self.label_entry.focus_set()  # Focus the label entry when a new rectangle is drawn
        elif not self.rect:
            # Focus the label entry if an existing rectangle is clicked and still selected
            if self.currently_selected:
                self.label_entry.focus_set()

    def add_label(self, event=None):
        if self.currently_selected and self.label_entry.get().strip():
            label = self.label_entry.get().strip().upper()
            coords = self.canvas.coords(self.currently_selected)
            self.annotations[self.currently_selected] = {
                'label': label, 'coordinates': coords}
            x1, y1, _, _ = coords
            self.canvas.create_text(
                x1, y1, anchor='nw', text=label, font=("Purisa", 10), fill="blue")
            self.label_entry.delete(0, tk.END)
            self.canvas.focus_set()  # Remove focus from the entry field after adding a label

    def deselect_current(self):
        if self.currently_selected not in self.annotations:
            # Remove rectangle if no label was added
            self.canvas.delete(self.currently_selected)
        else:
            self.canvas.itemconfig(self.currently_selected, outline='red')
        self.currently_selected = None
        self.btn_label.config(state=tk.DISABLED)

    def save_annotations(self):
        with open("annotations.json", "w") as file:
            json.dump(self.annotations, file, indent=4)
        print("Annotations saved!")


if __name__ == "__main__":
    root = tk.Tk()
    app = AnnotationTool(root)
    root.mainloop()
