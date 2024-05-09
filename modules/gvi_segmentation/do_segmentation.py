import matplotlib.pyplot as plt
import numpy as np
import torch
from PIL import Image
from transformers import AutoImageProcessor, Mask2FormerForUniversalSegmentation

# Color palette to map each class to a RGB value
color_palette = [
    [128, 64, 128],  # 0: road - maroon
    [244, 35, 232],  # 1: sidewalk - pink
    [70, 70, 70],  # 2: building - dark gray
    [102, 102, 156],  # 3: wall - purple
    [190, 153, 153],  # 4: fence - light brown
    [153, 153, 153],  # 5: pole - gray
    [250, 170, 30],  # 6: traffic light - orange
    [220, 220, 0],  # 7: traffic sign - yellow
    [0, 255, 0],  # 8: vegetation - dark green
    [152, 251, 152],  # 9: terrain - light green
    [70, 130, 180],  # 10: sky - blue
    [220, 20, 60],  # 11: person - red
    [255, 0, 0],  # 12: rider - bright red
    [0, 0, 142],  # 13: car - dark blue
    [0, 0, 70],  # 14: truck - navy blue
    [0, 60, 100],  # 15: bus - dark teal
    [0, 80, 100],  # 16: train - dark green
    [0, 0, 230],  # 17: motorcycle - blue
    [119, 11, 32],  # 18: bicycle - dark red
]


def get_models():
    # Load the pretrained AutoImageProcessor from the "facebook/mask2former-swin-large-cityscapes-semantic" model
    processor = AutoImageProcessor.from_pretrained(
        "facebook/mask2former-swin-large-cityscapes-semantic"
    )
    # Set the device to GPU if available, otherwise use CPU
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    # Load the pretrained Mask2FormerForUniversalSegmentation model from "facebook/mask2former-swin-large-cityscapes-semantic"
    model = Mask2FormerForUniversalSegmentation.from_pretrained(
        "facebook/mask2former-swin-large-cityscapes-semantic"
    )
    # Move the model to the specified device (GPU or CPU)
    model = model.to(device)
    # Return the processor and model as a tuple
    return processor, model


def segment_images(image, processor, model):
    # Preprocess the image using the image processor
    inputs = processor(images=image, return_tensors="pt")
    # Perform a forward pass through the model to obtain the segmentation
    with torch.no_grad():
        # Check if a GPU is available
        if torch.cuda.is_available():
            # Move the inputs to the GPU
            inputs = {k: v.to("cuda") for k, v in inputs.items()}
            # Perform the forward pass through the model
            outputs = model(**inputs)
            # Post-process the semantic segmentation outputs using the processor and move the results to CPU
            segmentation = processor.post_process_semantic_segmentation(
                outputs, target_sizes=[image.size[::-1]]
            )[0].to("cpu")
        else:
            # Perform the forward pass through the model
            outputs = model(**inputs)
            # Post-process the semantic segmentation outputs using the processor
            segmentation = processor.post_process_semantic_segmentation(
                outputs, target_sizes=[image.size[::-1]]
            )[0]
    return segmentation


def crop_panoramic_images(image, segmentation):
    width, height = image.size
    w4 = int(width / 4)
    h4 = int(height / 4)
    hFor43 = int(w4 * 3 / 4)
    images = []
    pickles = []
    # Crop the panoramic image based on road centers
    for w in range(4):
        x_begin = w * w4
        x_end = (w + 1) * w4
        cropped_image = image.crop((x_begin, h4, x_end, h4 + hFor43))
        cropped_segmentation = segmentation[h4 : h4 + hFor43, x_begin:x_end]
        images.append(cropped_image)
        pickles.append(cropped_segmentation)
    return images, pickles


def get_GVI(segmentations):
    total_pixels = 0
    vegetation_pixels = 0
    segment_scores = []
    for segment in segmentations:
        # Calculate the total number of pixels in the segmentation
        total_pixels += segment.numel()
        # Filter the pixels that represent vegetation (label 8) and count them
        vegetation_pixels += (segment == 8).sum().item()

        curr_segment_score = (segment == 8).sum().item() / segment.numel()
        segment_scores.append(curr_segment_score)

    # Calculate the percentage of green pixels in the segmentation
    return (vegetation_pixels / total_pixels), segment_scores


def process_images_simple(image_url, processor, model):
    try:
        # Fetch and process the image
        # image = Image.open(requests.get(image_url, stream=True).raw)
        image = Image.open(image_url)
        # Get the size of the image
        width, height = image.size
        # Crop the bottom 20% of the image to remove the band at the bottom of the panoramic image
        bottom_crop = int(height * 0.2)
        image = image.crop((0, 0, width, height - bottom_crop))
        # Apply the semantic segmentation to the image
        segmentation = segment_images(image, processor, model)
        # Cut panoramic image in 4 equal parts
        # Crop the image and its segmentation based on the previously found road centers
        images, pickles = crop_panoramic_images(image, segmentation)
        # Calculate the Green View Index (GVI) for the cropped segmentations
        GVI, segment_scores = get_GVI(pickles)
        return images, pickles, GVI, segment_scores
    except:
        # If there was an error while processing the image, set the "error" flag to true and continue with other images
        return None, None, None, None


def visualize_results_pil(image, segmentation, num):
    fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, figsize=(9, 4), sharey=True)
    # Display the widened panorama image
    ax1.imshow(image)
    ax1.set_title("Image")
    ax1.axis("off")
    # Map the segmentation result to the color palette
    seg_color = np.zeros(segmentation.shape + (3,), dtype=np.uint8)
    for label, color in enumerate(color_palette):
        seg_color[segmentation == label] = color
    # Display the colored segmentation result
    ax2.imshow(seg_color)
    ax2.set_title("Segmentation")
    ax2.axis("off")
    fig.savefig(
        f"tmp{num}.png",
        bbox_inches="tight",
        dpi=100,
    )
    print("tmp.png")
    new_image = Image.open(f"tmp{num}.png")
    return new_image


def save_images_pil(images, segmentation):
    new_images = []
    for index, image in enumerate(images):
        curr_segment = segmentation[index]
        new_image = visualize_results_pil(image, curr_segment, index)
        new_images.append(new_image)
    return new_images


def segmentation_pipeline(image_url):
    # Get the image processor and model
    processor, model = get_models()
    # Process the image
    images, segmentation, GVI, segment_scores = process_images_simple(
        image_url, processor, model
    )
    # Save the images
    new_images = save_images_pil(images, segmentation)
    print(GVI)
    print(segment_scores)
    return new_images, GVI, segment_scores


if __name__ == "__main__":
    example_image = "example_image_street_view.jpg"
    segmentation_pipeline(example_image)
