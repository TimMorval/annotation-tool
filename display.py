import cv2
import json


def display_predictions(json_path: str):
    with open(json_path) as f:
        data_json = f.read()

    # Parse JSON
    data = json.loads(data_json)

    # Load the image
    image_path = data["data"]["ocr"]
    image = cv2.imread(image_path)

    # Check if image was loaded
    if image is None:
        print("Error loading image")
    else:
        # Process each bounding box and text
        for prediction in data['predictions']:
            for result in prediction['result']:
                # Extract values
                x = result['value']['x']
                y = result['value']['y']
                width = result['value']['width']
                height = result['value']['height']
                if "text" not in result['value']:
                    continue
                text = result['value']['text']

                # Convert percentages to pixel coordinates (if your coordinates are percentages)
                img_height, img_width, _ = image.shape
                rect_x = int((x / 100) * img_width)
                rect_y = int((y / 100) * img_height)
                rect_width = int((width / 100) * img_width)
                rect_height = int((height / 100) * img_height)

                # Draw rectangle
                cv2.rectangle(image, (rect_x, rect_y), (rect_x +
                                                        rect_width, rect_y + rect_height), (0, 255, 0), 2)

                # Add text
                cv2.putText(image, text, (rect_x, rect_y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)

        # Show the result
        cv2.imshow("Annotated Image", image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    json_path = "predictions/CANVA_03_02_2024.json"
    display_predictions(json_path)
