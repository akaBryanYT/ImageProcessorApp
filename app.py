import os
import io
import uuid
from flask import Flask, request, render_template, send_file, flash, redirect, url_for
from PIL import Image, ImageOps, UnidentifiedImageError

# ──────────────────────────────────────────────────────────────────────────────
# Flask setup
# ──────────────────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "a-default-very-secret-key")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}


def allowed_file(filename: str) -> bool:
    """Return True if the filename extension is one we accept."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ──────────────────────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────────────────────
@app.route("/", methods=["GET"])
def index():
    """Render the upload/processing form."""
    return render_template("index.html")


@app.route("/process", methods=["POST"])
def process_image():
    """Handle an upload, perform processing, and stream the result back."""
    # ---------- File sanity checks ----------
    if "file" not in request.files:
        flash("No file part")
        return redirect(url_for("index"))

    file = request.files["file"]

    if file.filename == "":
        flash("No selected file")
        return redirect(url_for("index"))

    if not allowed_file(file.filename):
        flash("Invalid file type. Allowed types: png, jpg, jpeg, gif")
        return redirect(url_for("index"))

    # ---------- Pull form controls ----------
    try:
        target_width = request.form.get("width", type=int)
        resize_option = request.form.get("resize_option", "width")  # width • percent • none
        percentage = request.form.get("percentage", 100, type=int)
        apply_grayscale = "grayscale" in request.form
        apply_sepia = "sepia" in request.form
        output_format = request.form.get("format", "JPEG").upper()
        if output_format not in {"JPEG", "PNG", "GIF"}:
            output_format = "JPEG"
    except ValueError:  # never really triggered but kept as guard-rail
        flash("Invalid input for dimensions or percentage.")
        return redirect(url_for("index"))

    # ---------- Validate width / percent ----------
    if resize_option == "width":
        if target_width is None or target_width <= 0:
            flash("Invalid input for dimensions")
            return redirect(url_for("index"))

    if resize_option == "percent":
        if percentage is None or percentage <= 0:
            flash(
                "Percentage resulted in zero or negative image dimension, original size kept."
            )
            resize_option = "none"  # fall back to original size

    # ---------- Perform processing ----------
    try:
        img = Image.open(file.stream)
        processed_img = process_image_data(
            img,
            resize_option=resize_option,
            target_width=target_width,
            percentage=percentage,
            apply_grayscale=apply_grayscale,
            apply_sepia=apply_sepia,
        )

        # ---------- Stream the file back ----------
        img_io = io.BytesIO()
        save_kwargs = {"format": output_format}
        if output_format == "JPEG":
            # JPEG must be RGB
            if processed_img.mode in {"RGBA", "P"}:
                processed_img = processed_img.convert("RGB")
            save_kwargs["quality"] = 90

        processed_img.save(img_io, **save_kwargs)
        img_io.seek(0)

        original_stem, _ = os.path.splitext(file.filename)
        safe_name = f"{original_stem}_{uuid.uuid4().hex[:8]}.{output_format.lower()}"

        return send_file(
            img_io,
            mimetype=f"image/{output_format.lower()}",
            as_attachment=True,
            download_name=safe_name,
        )

    except UnidentifiedImageError:
        flash("Cannot identify image file. It might be corrupted or an unsupported format.")
        return redirect(url_for("index"))
    except Exception as exc:
        app.logger.error("Error processing image", exc_info=True)
        flash(f"An error occurred during processing: {exc}")
        return redirect(url_for("index"))


# ──────────────────────────────────────────────────────────────────────────────
# Pure-function image operations
# ──────────────────────────────────────────────────────────────────────────────
def process_image_data(
    img: Image.Image,
    resize_option: str,
    target_width: int | None,
    percentage: int,
    apply_grayscale: bool,
    apply_sepia: bool,
) -> Image.Image:
    """Resize and/or filter *img* according to the supplied options."""
    processed = img.copy()

    # ----- resizing -----
    ow, oh = processed.size
    if resize_option == "width" and target_width and target_width > 0 and ow != target_width:
        aspect = oh / ow
        new_size = (target_width, int(target_width * aspect))
        processed = processed.resize(new_size, Image.Resampling.LANCZOS)

    elif resize_option == "percent" and percentage > 0 and percentage != 100:
        scale = percentage / 100.0
        nw = max(1, int(ow * scale))
        nh = max(1, int(oh * scale))
        processed = processed.resize((nw, nh), Image.Resampling.LANCZOS)

    # ----- filters -----
    if apply_grayscale:
        processed = ImageOps.grayscale(processed)
    if apply_sepia:
        processed = apply_sepia_filter(processed)

    return processed


def apply_sepia_filter(img: Image.Image) -> Image.Image:
    """Return *img* with a naïve sepia tone applied."""
    if img.mode != "RGB":
        img = img.convert("RGB")

    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b = px[x, y]
            tr = min(255, int(0.393 * r + 0.769 * g + 0.189 * b))
            tg = min(255, int(0.349 * r + 0.686 * g + 0.168 * b))
            tb = min(255, int(0.272 * r + 0.534 * g + 0.131 * b))
            px[x, y] = (tr, tg, tb)
    return img


# ──────────────────────────────────────────────────────────────────────────────
# Dev server
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # DO NOT enable debug=True in production.
    app.run(host="0.0.0.0", port=5000, debug=True)