import streamlit as st
from PIL import Image, ImageDraw
import pandas as pd
from datetime import datetime
import io
import csv
import os

# Set page layout
st.set_page_config(layout="wide")

# --- Load Body Image (with fallback) ---
def load_body_image():
    # Try to find the image (case-insensitive)
    image_files = [f for f in os.listdir() if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    body_images = [f for f in image_files if "human" in f.lower() or "body" in f.lower()]

    if body_images:
        try:
            return Image.open(body_images[0]).convert("RGBA")
        except Exception as e:
            st.error(f"Error loading image '{body_images[0]}': {e}")
    else:
        # Fallback: Create a blank white image if no body image is found
        st.warning("No body outline image found. Using a blank placeholder.")
        return Image.new("RGBA", (500, 800), "white")

base_image = load_body_image()

# Initialize session state
if "dots" not in st.session_state:
    st.session_state.dots = []

if "entries" not in st.session_state:
    st.session_state.entries = []

# --- Function: Draw dots on the image ---
def get_image_with_dots(dots, current_dot=None):
    img = base_image.copy()
    draw = ImageDraw.Draw(img)
    for x, y in dots:
        r = 6
        draw.ellipse((x - r, y - r, x + r, y + r), fill="red")
    if current_dot:
        cx, cy = current_dot
        r = 6
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill="blue")  # Show current slider position in blue
    return img

# --- Sidebar: Label input and actions ---
with st.sidebar:
    st.header("Add Entry")
    label = st.text_input("Label for current dots")

    if st.button("Save Entry"):
        if label and st.session_state.dots:
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.entries.append((date, label, st.session_state.dots.copy()))
            st.session_state.dots = []
            st.success("Entry saved.")
        else:
            st.warning("Please add at least one dot and a label.")

    if st.button("Undo Last Dot"):
        if st.session_state.dots:
            st.session_state.dots.pop()

    if st.button("Clear All Dots"):
        st.session_state.dots.clear()

# --- Main area: Title and instructions ---
st.title("🧍 Body Marking Tool (Web App)")
st.markdown("Use the sliders to position a blue dot, then click 'Add Dot'.")

# --- Resize image to fit display ---
display_width = 500
if base_image.width > 0:
    w_percent = display_width / base_image.width
    display_height = int(base_image.height * w_percent)
else:
    display_height = 800  # Default height if base_image is blank

# --- Manual dot input (simulated clicking) ---
st.subheader("🔵 Position Dot")
x = st.slider("X coordinate", 0, base_image.width - 1 if base_image.width > 0 else 499, base_image.width // 2 if base_image.width > 0 else 250)
y = st.slider("Y coordinate", 0, base_image.height - 1 if base_image.height > 0 else 799, base_image.height // 2 if base_image.height > 0 else 400)

# --- Render image with existing dots and the current slider position ---
image_with_current_dot = get_image_with_dots(st.session_state.dots, (x, y))
img_bytes = io.BytesIO()
image_with_current_dot.save(img_bytes, format="PNG")
st.image(img_bytes.getvalue(), width=display_width)

if st.button("Add Dot"):
    st.session_state.dots.append((x, y))
    st.experimental_rerun() # Rerun to update the image with the permanent red dot

# --- Display saved entries ---
st.subheader("📋 Saved Entries")

if st.session_state.entries:
    df = pd.DataFrame([
        {"Date": date, "Label": label, "Dot Count": len(dots)}
        for date, label, dots in st.session_state.entries
    ])
    st.dataframe(df)

    for i, (date, label, dots) in enumerate(st.session_state.entries):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"**{label}** ({len(dots)} dots) — *{date}*")
        with col2:
            if st.button("❌ Delete", key=f"delete_{i}"):
                st.session_state.entries.pop(i)
                st.experimental_rerun()
else:
    st.info("No entries saved yet.")

# --- Save all to CSV ---
if st.button("📥 Export to CSV"):
    with open("body_markers_calendar.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Label", "Dots"])
        for date, label, dots in st.session_state.entries:
            writer.writerow([date, label, dots])
    st.success("Data saved to `body_markers_calendar.csv`.")