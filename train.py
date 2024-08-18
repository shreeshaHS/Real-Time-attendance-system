import os
import cv2
import numpy as np

recognizer = cv2.face.LBPHFaceRecognizer_create()  # Use LBPH Face Recognizer
path = "Main/static/captured_images"


def get_images_with_name(path):
    images_paths = [os.path.join(path, f) for f in os.listdir(path)]  # Set images path to os
    faces = []
    names = []
    for single_image_path in images_paths:
        faceImg = cv2.imread(single_image_path, cv2.IMREAD_GRAYSCALE)  # Read image in grayscale
        name = os.path.splitext(os.path.basename(single_image_path))[0]  # Extract name without extension
        faces.append(faceImg)
        names.append(name)
        cv2.imshow("Training", faceImg)
        cv2.waitKey(10)
    return names, faces


names, faces = get_images_with_name(path)

# Convert names to labels (integer indices)
unique_names = list(set(names))
label_map = {name: i for i, name in enumerate(unique_names)}
labels = np.array([label_map[name] for name in names])

recognizer.train(faces, labels)  # Pass labels as integer indices
recognizer.save('recognizer/Trainingdata.yml')
cv2.destroyAllWindows()
