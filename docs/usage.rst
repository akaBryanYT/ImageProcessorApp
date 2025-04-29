Usage Guide
===========

Follow these steps to use the Image Processor App:

1.  Navigate to the application URL provided by the deployment (e.g., ``http://<your-ec2-ip-address>``).
2.  Click **Choose Image** / **Browse...** and select a valid image file from your computer (.png, .jpg, .jpeg, .gif).
3.  Select the desired **Resize Options**:
    * **Resize by Width:** Check the radio button and enter the target width in pixels in the input field next to it.
    * **Resize by Percentage:** Check the radio button and enter the desired percentage (e.g., 50 for half size, 200 for double size) in the input field.
    * **Keep Original Size:** Check this radio button if no resizing is needed.
4.  Select **Filter Options** by checking the boxes:
    * **Grayscale:** Converts the image to black and white.
    * **Sepia:** Applies a warm brown tone filter.
    * (You can select both, though applying Sepia after Grayscale might not have the desired effect).
5.  Select the desired **Output Format** from the dropdown menu (JPEG, PNG, or GIF).
6.  Click the **Process Image** button.
7.  After a short processing time, your browser should prompt you to download the modified image file. The filename will typically include the original name plus a unique identifier and the new extension.

Input Considerations
--------------------
* **Allowed File Types:** Only `.png`, `.jpg`, `.jpeg`, and `.gif` files are accepted.
* **Max Upload Size:** The server is configured to accept files up to 50MB (this limit is set in the Nginx configuration). Larger files will result in an error.
* **Dimensions:** Ensure width/percentage values are reasonable positive numbers. Very large dimensions might consume significant server resources or fail.