import tkinter as tk
from tkinter import Frame, filedialog, Label
from tkinter import messagebox
from PIL import Image, ImageTk
import json


class AnnotationTool:
    def __init__(self, root: Frame):
        self.root = root
        self.root.title("Image Annotation Tool")

        # Setting up the scrolling canvas
        self.canvas_frame = tk.Frame(root)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.canvas_frame, bg="white")
        self.x_scroll = tk.Scrollbar(
            self.canvas_frame, orient="horizontal", command=self.canvas.xview)
        self.y_scroll = tk.Scrollbar(
            self.canvas_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=self.x_scroll.set,
                              yscrollcommand=self.y_scroll.set)

        self.x_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Enabling mousewheel scrolling
        # For Windows and Linux
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        # For Linux, scrolling up
        self.canvas.bind("<Button-4>", self.on_mousewheel)
        # For Linux, scrolling down
        self.canvas.bind("<Button-5>", self.on_mousewheel)
        self.root.bind("<Command-MouseWheel>", self.on_mousewheel)  # For macOS

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

        self.btn_delete = tk.Button(
            root, text="Delete", command=self.delete_selected, state=tk.DISABLED)
        self.btn_delete.pack(side=tk.LEFT)

        label_label = Label(root, text="Label:")
        label_label.pack(side=tk.LEFT)
        self.label_entry = tk.Entry(root)
        self.label_entry.pack(side=tk.LEFT)

        text_label = Label(root, text="Text:")
        text_label.pack(side=tk.LEFT)
        self.text_entry = tk.Entry(root)
        self.text_entry.pack(side=tk.LEFT)

        self.btn_label = tk.Button(
            root, text="Add Annotation", command=self.add_label, state=tk.DISABLED)
        self.btn_label.pack(side=tk.LEFT)

        # Bind mouse events
        self.canvas.bind("<ButtonPress-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

    def on_mousewheel(self, event):
        # Shift+MouseWheel for horizontal on Windows and Linux
        if event.state == 1 or event.num in (4, 5):
            if event.num == 4 or event.delta > 0:  # Wheel scrolled up
                self.canvas.xview_scroll(-1, "units")
            elif event.num == 5 or event.delta < 0:  # Wheel scrolled down
                self.canvas.xview_scroll(1, "units")
        else:
            # MouseWheel scrolling for vertical
            if event.num == 4 or event.delta > 0:  # Wheel scrolled up
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5 or event.delta < 0:  # Wheel scrolled down
                self.canvas.yview_scroll(1, "units")

    def load_image(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.img = Image.open(file_path)
            self.tk_img = ImageTk.PhotoImage(self.img)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_img)
            self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

    def on_click(self, event):
        # Convert canvas coordinates to window coordinates
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        self.rect = None
        for rect in self.canvas.find_withtag("rectangle"):
            x1, y1, x2, y2 = self.canvas.coords(rect)
            if x1 <= self.start_x <= x2 and y1 <= self.start_y <= y2:
                if self.currently_selected:
                    self.deselect_current()
                self.currently_selected = rect
                self.canvas.itemconfig(rect, outline='green')
                self.btn_label.config(state=tk.NORMAL)
                self.btn_delete.config(state=tk.NORMAL)
                # Set the entry fields with the existing label and text
                annotation_data = self.annotations.get(rect)
                if annotation_data:
                    self.label_entry.delete(0, tk.END)
                    self.label_entry.insert(0, annotation_data['label'])
                    self.text_entry.delete(0, tk.END)
                    self.text_entry.insert(0, annotation_data['text'])
                return
        if self.currently_selected:
            self.deselect_current()

    def on_drag(self, event):
        if not self.rect:
            curX = self.canvas.canvasx(event.x)
            curY = self.canvas.canvasy(event.y)
            self.rect = self.canvas.create_rectangle(
                self.start_x, self.start_y, curX, curY, outline='green', tags="rectangle")
        else:
            curX = self.canvas.canvasx(event.x)
            curY = self.canvas.canvasy(event.y)
            self.canvas.coords(self.rect, self.start_x,
                               self.start_y, curX, curY)

    def on_release(self, event):
        if self.rect:
            self.canvas.itemconfig(self.rect, outline='green')
            self.btn_label.config(state=tk.NORMAL)
            self.btn_delete.config(state=tk.NORMAL)
            self.label_entry.focus_set()
            self.currently_selected = self.rect

    def add_label(self, event=None):
        if self.currently_selected and self.label_entry.get().strip() and self.text_entry.get().strip():
            label = self.label_entry.get().strip().upper()
            text = self.text_entry.get().strip()
            coords = self.canvas.coords(self.currently_selected)
            # Update the annotations with label and additional text
            self.annotations[self.currently_selected] = {
                'label': label,
                'text': text,
                'coordinates': coords,
                'text_id': self.annotations.get(self.currently_selected, {}).get('text_id')
            }
            # Update the text display on the canvas
            self.update_canvas_text(coords, f"{text}, {label}")
            self.label_entry.delete(0, tk.END)
            self.text_entry.delete(0, tk.END)

            # Unfocus and deselect the current selection
            self.deselect_current()
        else:
            messagebox.showerror(
                "Error", "Please make sure a rectangle is selected and text fields are not empty.")

    def update_canvas_text(self, coords, text):
        text_id = self.annotations[self.currently_selected].get('text_id')
        if text_id:
            self.canvas.delete(text_id)
        new_text_id = self.canvas.create_text(
            coords[0], coords[1], anchor='nw', text=text, font=("Purisa", 10), fill="blue")
        self.annotations[self.currently_selected]['text_id'] = new_text_id

    def deselect_current(self):
        if self.currently_selected not in self.annotations or 'label' not in self.annotations[self.currently_selected]:
            # Remove rectangle if no label was added
            self.canvas.delete(self.currently_selected)
        else:
            self.canvas.itemconfig(self.currently_selected, outline='red')
        self.currently_selected = None
        self.btn_label.config(state=tk.DISABLED)
        self.btn_delete.config(state=tk.DISABLED)

    def delete_selected(self):
        if self.currently_selected:
            # Delete the label text from canvas
            if self.currently_selected in self.annotations:
                label_id = self.annotations[self.currently_selected].get(
                    'text_id')
                if label_id:
                    self.canvas.delete(label_id)
            # Delete the rectangle
            self.canvas.delete(self.currently_selected)
            # Remove from annotations dictionary
            if self.currently_selected in self.annotations:
                del self.annotations[self.currently_selected]
            self.currently_selected = None
            self.btn_label.config(state=tk.DISABLED)
            self.btn_delete.config(state=tk.DISABLED)

    def save_annotations(self):
        if self.annotations:
            formatted_annotations = [{
                "id": key,
                "label": value['label'],
                "text": value['text'],
                "coordinates": value['coordinates'],
                "text_id": value['text_id']
            } for key, value in self.annotations.items()]
            with open("annotations.json", "w") as file:
                json.dump(formatted_annotations, file, indent=4)
            messagebox.showinfo("Success", "Annotations saved!")
        else:
            messagebox.showerror("Save Error", "No annotations to save.")


if __name__ == "__main__":
    root = tk.Tk()
    app = AnnotationTool(root)
    root.mainloop()
