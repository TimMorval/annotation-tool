from textwrap import dedent
import tkinter as tk
from tkinter import Tk, filedialog, Label
from tkinter import messagebox
from uuid import uuid4
from PIL import Image, ImageTk
import json
import os
import shutil


class AnnotationTool:
    def __init__(self, root: Tk, done_folder: str = "done"):
        self.setup_main_window(root)
        self.create_canvas()
        self.create_scrollbars()
        self.setup_bindings()
        self.setup_annotation_controls()
        self.initialize_annotation_data()
        self.precision = 1e-2
        self.done_folder = done_folder

    def setup_main_window(self, root):
        self.root = root
        self.root.title("Image Annotation Tool")
        self.canvas_frame = tk.Frame(root)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)

    def create_canvas(self):
        self.canvas = tk.Canvas(self.canvas_frame, bg="white")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def create_scrollbars(self):
        self.x_scroll = tk.Scrollbar(
            self.canvas_frame, orient="horizontal", command=self.canvas.xview)
        self.y_scroll = tk.Scrollbar(
            self.canvas_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=self.x_scroll.set,
                              yscrollcommand=self.y_scroll.set)
        self.x_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.y_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def setup_bindings(self):
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind("<Button-4>", self.on_mousewheel)
        self.canvas.bind("<Button-5>", self.on_mousewheel)
        self.root.bind("<Command-MouseWheel>",
                       self.on_mousewheel)  # macOS specific
        self.canvas.bind("<ButtonPress-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.root.bind(
            "<Command-l>", lambda event: self.load_annotations())  # Load
        self.root.bind(
            "<Command-s>", lambda event: self.save_annotations())  # Save
        self.root.bind(
            "<Command-d>", lambda event: self.delete_selected())  # Delete

    def setup_annotation_controls(self):
        btn_load = tk.Button(
            self.root, text="Load Annotations", command=self.load_annotations)
        btn_load.pack(side=tk.LEFT)
        btn_save = tk.Button(
            self.root, text="Save Annotations", command=self.save_annotations)
        btn_save.pack(side=tk.LEFT)
        self.btn_delete = tk.Button(
            self.root, text="Delete", command=self.delete_selected, state=tk.DISABLED)
        self.btn_delete.pack(side=tk.LEFT)
        self.btn_done = tk.Button(
            self.root, text="Done", command=self.move_to_done)
        self.btn_done.pack(side=tk.LEFT)
        label_label = Label(self.root, text="Label:")
        label_label.pack(side=tk.LEFT)
        self.label_entry = tk.Entry(self.root)
        self.label_entry.pack(side=tk.LEFT)
        self.label_entry.bind("<Return>", self.add_label)
        text_label = Label(self.root, text="Text:")
        text_label.pack(side=tk.LEFT)
        self.text_entry = tk.Entry(self.root)
        self.text_entry.pack(side=tk.LEFT)
        self.text_entry.bind("<Return>", self.add_label)
        self.btn_label = tk.Button(
            self.root, text="Add Annotation", command=self.add_label, state=tk.DISABLED)
        self.btn_label.pack(side=tk.LEFT)

    def initialize_annotation_data(self):
        self.annotations_path = None
        self.img = None
        self.annotations = {}
        self.rect = None
        self.start_x = None
        self.start_y = None
        self.currently_selected = None

    def reset_ui(self):
        """Reset the UI components to a clean state."""
        self.canvas.delete("all")
        self.annotations = {}
        self.currently_selected = None
        self.label_entry.delete(0, tk.END)
        self.text_entry.delete(0, tk.END)
        self.btn_label.config(state=tk.DISABLED)
        self.btn_delete.config(state=tk.DISABLED)

    def on_mousewheel(self, event):
        if event.state == 1 or event.num in (4, 5):
            if event.num == 4 or event.delta > 0:
                self.canvas.xview_scroll(-1, "units")
            elif event.num == 5 or event.delta < 0:
                self.canvas.xview_scroll(1, "units")
        else:
            if event.num == 4 or event.delta > 0:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5 or event.delta < 0:
                self.canvas.yview_scroll(1, "units")

    def load_annotations(self):
        """Load annotations by asking user for file, reading it, and displaying annotations."""
        annotations_path = filedialog.askopenfilename(
            title="Select JSON Annotations File")
        if annotations_path:
            self.annotations_path = annotations_path
            try:
                self.refresh_annotations()
            except Exception as e:
                messagebox.showerror("Error Loading Annotations", str(e))

    def refresh_annotations(self):
        """Refresh the annotations on the canvas."""
        if self.annotations_path:
            annotations = self.read_annotation_data(self.annotations_path)
            self.reset_ui()
            self.display_image_and_annotations(annotations)
        else:
            messagebox.showerror("Could not reload annotations")

    def read_annotation_data(self, path):
        """Read and return annotation data from the specified file path."""
        with open(path, 'r') as file:
            self.annotations_path = path
            data = json.load(file)
            self.image_path = data['data']['ocr']
            self.img = Image.open(self.image_path)
            annotations = data['predictions'][0]['result']
            return annotations

    def display_image_and_annotations(self, annotations):
        """Display the image on the canvas and draw the loaded annotations."""
        try:
            self.tk_img = ImageTk.PhotoImage(self.img)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_img)
            self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
            self.draw_annotations(annotations)
        except Exception as e:
            raise RuntimeError("Failed to display annotations: " + str(e))

    def draw_annotations(self, annotations):
        """Draw annotations on the canvas."""
        for item in annotations:
            if item['type'] == 'textarea':
                self.draw_text_area_annotation(item)

    def draw_text_area_annotation(self, item):
        """Draw a text area annotation based on its description."""
        bbox = item['value']
        x1, y1, x2, y2 = self.calculate_bbox_coordinates(bbox)
        rect_id = self.canvas.create_rectangle(
            x1, y1, x2, y2, outline='red', tags="rectangle")
        text_x, text_y = x1, y1 - 12
        text_id = self.canvas.create_text(
            text_x, text_y, anchor='nw', text=dedent(f"{bbox['text']} ({bbox['label']})"),
            font=("Purisa", 10), fill="blue"
        )
        self.annotations[rect_id] = {
            'rect_id': rect_id, 'text_id': text_id,
            'value': bbox, 'text': bbox['text'], 'label': bbox['label']
        }

    def calculate_bbox_coordinates(self, bbox):
        """Calculate and return bounding box coordinates based on image dimensions."""
        x1 = bbox['x'] * self.img.width / 100
        y1 = bbox['y'] * self.img.height / 100
        x2 = x1 + (bbox['width'] * self.img.width / 100)
        y2 = y1 + (bbox['height'] * self.img.height / 100)
        return x1, y1, x2, y2

    def on_click(self, event):
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
                annotation_data = self.annotations[self.currently_selected]['value']
                if annotation_data:
                    self.label_entry.delete(0, tk.END)
                    self.label_entry.insert(
                        0, annotation_data['label'])
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
                self.start_x, self.start_y, curX, curY, outline="red", tags="rectangle")
        else:
            curX = self.canvas.canvasx(event.x)
            curY = self.canvas.canvasy(event.y)
            self.canvas.coords(self.rect, self.start_x,
                               self.start_y, curX, curY)

    def on_release(self, event):
        if self.rect:
            if self.rect not in self.annotations:
                bbox = self.format_bbox({
                    'x': self.start_x * 100 / self.img.width,
                    'y': self.start_y * 100 / self.img.height,
                    'width': (self.canvas.canvasx(event.x) - self.start_x) * 100 / self.img.width,
                    'height': (self.canvas.canvasy(event.y) - self.start_y) * 100 / self.img.height,
                    'rotation': 0
                })
                self.annotations[self.rect] = {
                    'rect_id': self.rect, 'text_id': None, 'value': bbox}
            self.canvas.itemconfig(self.rect, outline='green')
            self.btn_label.config(state=tk.NORMAL)
            self.btn_delete.config(state=tk.NORMAL)
            self.label_entry.focus_set()
            self.currently_selected = self.rect

    def format_bbox(self, bbox):
        x1 = bbox['x']
        y1 = bbox['y']
        x2 = x1 + bbox['width']
        y2 = y1 + bbox['height']
        x1, x2 = min(x1, x2), max(x1, x2)
        y1, y2 = min(y1, y2), max(y1, y2)
        new_bbox = {
            'x': x1,
            'y': y1,
            'width': x2-x1,
            'height': y2-y1,
            'rotation': 0
        }
        return new_bbox

    def add_label(self, event=None):
        if self.currently_selected and self.label_entry.get().strip() and self.text_entry.get().strip():
            label = self.label_entry.get().strip().upper()
            text = self.text_entry.get().strip()
            coords = self.canvas.coords(self.currently_selected)
            self.annotations[self.currently_selected]['value']['label'] = label
            self.annotations[self.currently_selected]['value']['text'] = text
            self.update_canvas_text(coords, f"{text} ({label})")
            self.label_entry.delete(0, tk.END)
            self.text_entry.delete(0, tk.END)
            self.deselect_current()
        else:
            messagebox.showerror(
                "Error", "Please make sure a rectangle is selected and text fields are not empty.")

    def update_canvas_text(self, coords, text):
        text_id = self.annotations[self.currently_selected]['text_id']
        if text_id:
            self.canvas.delete(text_id)
        new_text_id = self.canvas.create_text(
            coords[0], coords[1] - 12, anchor='nw', text=text, font=("Purisa", 10), fill="blue")
        self.annotations[self.currently_selected]['text_id'] = new_text_id

    def deselect_current(self):
        if self.currently_selected:
            if "label" in self.annotations[self.currently_selected]['value'] and "text" in self.annotations[self.currently_selected]['value']:
                self.canvas.itemconfig(self.currently_selected, outline='red')
            else:
                self.annotations.pop(self.currently_selected)
                self.canvas.delete(self.currently_selected)
        self.currently_selected = None
        self.btn_label.config(state=tk.DISABLED)
        self.btn_delete.config(state=tk.DISABLED)

    def delete_selected(self):
        if self.currently_selected:
            if self.currently_selected in self.annotations:
                label_id = self.annotations[self.currently_selected].get(
                    'text_id')
                if label_id:
                    self.canvas.delete(label_id)
                self.canvas.delete(self.currently_selected)
                del self.annotations[self.currently_selected]
            self.currently_selected = None
            self.btn_label.config(state=tk.DISABLED)
            self.btn_delete.config(state=tk.DISABLED)

    def format_annotations(self):
        """Format annotations for exporting, ensuring that only valid annotations are included."""
        results = [self.format_single_annotation(
            annotation) for annotation in self.annotations.values() if self.is_annotation_valid(annotation)]
        # Flatten the list and remove None
        results = [item for sublist in results for item in sublist if sublist]
        return {
            'data': {'ocr': self.img.filename},
            'predictions': [{'result': results, 'score': 100}]
        }

    def is_annotation_valid(self, annotation):
        """Check if an annotation is valid based on its content and dimensions."""
        annot_value = annotation['value']
        return annot_value['text'].strip() and annot_value['label'] and annot_value['height'] > self.precision and annot_value['width'] > self.precision

    def format_single_annotation(self, annotation):
        """Format a single annotation into the required dictionary format for bbox and transcription."""
        annot_value = annotation['value']
        region_id = str(uuid4())[:10]
        bbox = {key: annot_value[key] for key in ['x', 'y', 'width', 'height']}
        bbox['rotation'] = 0

        return [
            {
                'id': region_id, 'from_name': 'bbox', 'to_name': 'image', 'type': 'rectangle',
                'value': bbox
            },
            {
                'id': region_id, 'from_name': 'transcription', 'to_name': 'image', 'type': 'textarea',
                'value': {**bbox, 'text': annot_value['text'], 'label': annot_value['label']}
            }
        ]

    def save_annotations(self):
        """Saves the annotations to a file."""
        if self.annotations:
            formatted_annotations = self.format_annotations()
            with open(self.annotations_path, "w") as file:
                json.dump(formatted_annotations, file, indent=4)
            messagebox.showinfo("Success", "Annotations saved!")
            self.refresh_annotations()
        else:
            messagebox.showerror("Save Error", "No annotations to save.")

    def move_to_done(self):
        """Move the selected annotation file to the done folder."""
        if self.annotations_path:
            done_path = os.path.join(
                self.done_folder, os.path.basename(self.annotations_path))
            os.makedirs(self.done_folder, exist_ok=True)
            shutil.move(self.annotations_path, done_path)
            messagebox.showinfo("Success", f"Moved to {self.done_folder}")
            self.reset_ui()
        else:
            messagebox.showerror("Move Error", "No file to move.")


if __name__ == "__main__":
    root = tk.Tk()
    app = AnnotationTool(root)
    root.mainloop()
