import os
from flask import Flask, request, render_template, send_file, flash, redirect, url_for
from PIL import Image, ImageOps, UnidentifiedImageError
import io
import uuid # To generate unique filenames for safety

app = Flask(__name__)
# Secret key is needed for flashing messages
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'a-default-very-secret-key')
# Optional: configure upload folder and allowed extensions
# UPLOAD_FOLDER = 'uploads'
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET'])
def index():
    """Renders the main page."""
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_image():
    """Handles image upload, processing, and returns the modified image."""
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('index'))

    file = request.files['file']

    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('index'))

    if not file or not allowed_file(file.filename):
         flash('Invalid file type. Allowed types: png, jpg, jpeg, gif')
         return redirect(url_for('index'))

    # Get processing options from the form
    try:
        # Use get with default values for robustness
        target_width = request.form.get('width', type=int) # Expect integer width
        resize_option = request.form.get('resize_option', 'width') # 'width', 'percent', 'none'
        percentage = request.form.get('percentage', 100, type=int) # Default to 100% if not provided
        apply_grayscale = 'grayscale' in request.form
        apply_sepia = 'sepia' in request.form # Example filter
        output_format = request.form.get('format', 'JPEG').upper() # Default to JPEG

        if output_format not in ['JPEG', 'PNG', 'GIF']:
            output_format = 'JPEG' # Fallback to default if invalid format provided

    except ValueError:
         flash('Invalid input for dimensions or percentage.')
         return redirect(url_for('index'))

    try:
        img = Image.open(file.stream)
        original_format = img.format # Store original format if needed later

        # --- Image Processing Logic ---
        processed_img = process_image_data(img, resize_option, target_width, percentage, apply_grayscale, apply_sepia)

        # --- Prepare file for sending ---
        img_io = io.BytesIO()
        # Determine save format and parameters
        save_kwargs = {}
        if output_format == 'JPEG':
            # Ensure image mode is compatible with JPEG (e.g., convert RGBA to RGB)
            if processed_img.mode == 'RGBA' or processed_img.mode == 'P': # P is palette mode (like GIF)
                processed_img = processed_img.convert('RGB')
            save_kwargs['format'] = 'JPEG'
            save_kwargs['quality'] = 90 # Set JPEG quality
        elif output_format == 'PNG':
             save_kwargs['format'] = 'PNG'
        elif output_format == 'GIF':
             save_kwargs['format'] = 'GIF'
             # GIF saving might have specific options if needed
        else: # Fallback just in case
             processed_img = processed_img.convert('RGB') # Convert to RGB for safety
             save_kwargs['format'] = 'JPEG'

        processed_img.save(img_io, **save_kwargs)
        img_io.seek(0)

        # Generate a safe filename
        original_filename, original_extension = os.path.splitext(file.filename)
        safe_filename = f"{original_filename}_{uuid.uuid4().hex[:8]}.{output_format.lower()}"

        return send_file(
            img_io,
            mimetype=f'image/{output_format.lower()}',
            as_attachment=True, # Force download
            download_name=safe_filename # Suggest a filename
        )

    except UnidentifiedImageError:
        flash('Cannot identify image file. It might be corrupted or an unsupported format.')
        return redirect(url_for('index'))
    except Exception as e:
        app.logger.error(f"Error processing image: {e}", exc_info=True) # Log the error
        flash(f'An error occurred during processing: {e}')
        return redirect(url_for('index'))

# --- Refactored Image Processing Logic ---
def process_image_data(img, resize_option, target_width, percentage, apply_grayscale, apply_sepia):
    """Applies resizing and filters to the PIL Image object."""
    processed_img = img.copy() # Work on a copy

    # --- Resizing ---
    original_width, original_height = processed_img.size
    new_width, new_height = original_width, original_height

    if resize_option == 'width' and target_width is not None and target_width > 0:
        if original_width != target_width: # Only resize if different
            aspect_ratio = original_height / original_width
            new_width = target_width
            new_height = int(new_width * aspect_ratio)
            processed_img = processed_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    elif resize_option == 'percent' and percentage is not None and 0 < percentage <= 500: # Added upper limit
        if percentage != 100: # Only resize if not 100%
            scale = percentage / 100.0
            new_width = int(original_width * scale)
            new_height = int(original_height * scale)
            if new_width > 0 and new_height > 0: # Ensure dimensions are valid
                processed_img = processed_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            else:
                # Handle edge case of scaling down too much, maybe keep original size or flash error
                flash('Percentage resulted in zero or negative image dimension, original size kept.') # Inform user

    # --- Filtering ---
    if apply_grayscale:
        # Convert to grayscale. 'L' mode is luminance (grayscale).
        processed_img = ImageOps.grayscale(processed_img)
        # Grayscale might remove alpha channel, need conversion back if PNG output needed with transparency later
        # However, grayscale itself doesn't have transparency. If original had alpha, it's lost here.

    if apply_sepia:
        processed_img = apply_sepia_filter(processed_img) # Apply sepia filter

    return processed_img

def apply_sepia_filter(img):
    """Applies a sepia filter to a PIL Image."""
    # Ensure image is in RGB mode for sepia calculation
    if img.mode != 'RGB':
        img = img.convert('RGB')

    width, height = img.size
    pixels = img.load() # Create the pixel map

    for py in range(height):
        for px in range(width):
            r, g, b = img.getpixel((px, py))

            tr = int(0.393 * r + 0.769 * g + 0.189 * b)
            tg = int(0.349 * r + 0.686 * g + 0.168 * b)
            tb = int(0.272 * r + 0.534 * g + 0.131 * b)

            # Clamp values to 0-255
            tr = min(255, tr)
            tg = min(255, tg)
            tb = min(255, tb)

            pixels[px, py] = (tr, tg, tb)
    return img

if __name__ == '__main__':
    # Use 0.0.0.0 to be accessible externally if needed (e.g., within Docker)
    # Debug=True enables auto-reloading and provides debugger (DO NOT use in production)
    app.run(host='0.0.0.0', port=5000, debug=True)