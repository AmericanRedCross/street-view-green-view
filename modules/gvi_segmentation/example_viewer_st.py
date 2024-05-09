import streamlit as st

from do_segmentation import segmentation_pipeline

st.set_page_config(layout="wide")
st.title("Green View Index Segmentation Viewer")
image = st.file_uploader("Upload an image", type=["jpg", "png"])

if image:
    st.image(image)

if st.button("Get GVI Index"):
    if image:
        new_images, GVI, segment_scores = segmentation_pipeline(image)

        # New columns
        col1, col2 = st.columns(2)

        col1.image(new_images[0], caption=f"Green View Index: {segment_scores[0]}")
        col2.image(new_images[1], caption=f"Green View Index: {segment_scores[1]}")

        col1.image(new_images[2], caption=f"Green View Index: {segment_scores[2]}")
        col2.image(new_images[3], caption=f"Green View Index: {segment_scores[3]}")

        st.success(f"Total Green View Index: {GVI}")

    else:
        st.error("Please upload an image")
