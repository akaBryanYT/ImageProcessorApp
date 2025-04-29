API Reference & Data Model
==========================

The application exposes a simple HTTP interface.

.. http:get:: /

    Serves the main HTML page of the application.

    :reqheader Accept: Usually ``text/html``.
    :resheader Content-Type: ``text/html; charset=utf-8``.
    :status 200: On success.

.. http:post:: /process

    Handles the image upload and processing request. This endpoint expects a request body with ``Content-Type: multipart/form-data``.

    **Request Form Data Parameters:**

    =================  ========  ======================================================================
    Parameter          Type      Description
    =================  ========  ======================================================================
    ``file``           File      **Required.** The image file to be processed.
    ``resize_option``  String    Controls resizing: 'width', 'percent', or 'none'. Default: 'width'.
    ``width``          Integer   Target width in pixels (used if ``resize_option`` is 'width').
    ``percentage``     Integer   Target percentage (used if ``resize_option`` is 'percent'). Default: 100.
    ``grayscale``      String    Checkbox value (e.g., 'true' or 'on') if grayscale is selected.
    ``sepia``          String    Checkbox value (e.g., 'true' or 'on') if sepia is selected.
    ``format``         String    Output format: 'JPEG', 'PNG', or 'GIF'. Default: 'JPEG'.
    =================  ========  ======================================================================

    **Responses:**

    * **Success (Status Code 200):**
        The response body contains the binary data of the processed image.
        :resheader Content-Type: ``image/jpeg``, ``image/png``, or ``image/gif``, depending on the requested format.
        :resheader Content-Disposition: ``attachment; filename="processed_image.ext"`` (suggests a download filename).

    * **Client Error (Status Code 302 Found):**
        Usually indicates an issue with the user's input (e.g., no file uploaded, invalid file type, invalid dimension values). The user is redirected back to the index page (``/``).
        A flash message containing the specific error details should be displayed on the index page after the redirect.

    * **Server Error (Status Code 500 Internal Server Error - or redirect 302 with generic error flash):**
        Indicates an unexpected error during processing on the server (e.g., Pillow library issue, file system problem). A generic error flash message might be shown after redirecting to index. Server logs should contain more details.

    **Data Model / Schema Summary:**

    * **Input:** ``multipart/form-data`` request containing binary image data and string key-value pairs for processing options.
    * **Output (Success):** Raw binary image stream (JPEG, PNG, or GIF) with appropriate headers for download.
    * **Output (Error):** HTTP Redirect (302) to the main page, with error details potentially conveyed via flashed messages rendered in the HTML.

Backend Module Documentation
----------------------------

Key functions involved in processing:

.. automodule:: app
    :members: process_image_data, apply_sepia_filter, allowed_file
    :undoc-members:
    :show-inheritance:

*(Ensure these functions in `app.py` have clear docstrings for `autodoc` to pick up)*