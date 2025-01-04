from PIL import Image, ImageDraw, ImageFilter, ImageSequence

def mask_rounded_corners(pil_img, corner_radius=30, blur_radius=0):
    """
    Adds an RGBA mask to 'pil_img' so that pixels outside the rounded rectangle are transparent.
    * corner_radius: Radius (in pixels) for corner rounding.
    * blur_radius: Optional blur on edges (though in a GIF you won't really get partial transparency).
    """
    # Ensure RGBA so we can put an alpha channel
    pil_img = pil_img.convert("RGBA")
    w, h = pil_img.size

    # Create a grayscale ("L") mask, same size
    mask = Image.new("L", (w, h), 0)

    # Since pillow >= 8.2, we can use draw.rounded_rectangle.
    # Or we can manually draw arcs + rectangles for older PIL versions.
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, w, h), radius=corner_radius, fill=255)

    # Optionally blur the mask to soften edges (though GIF won't show partial alpha)
    if blur_radius > 0:
        mask = mask.filter(ImageFilter.GaussianBlur(blur_radius))

    # Apply this mask as the alpha channel
    result = pil_img.copy()
    result.putalpha(mask)
    return result

def transparent_indexed_gif_frame(rgba_frame):
    """
    Takes an RGBA Image, converts it to a paletted (P) mode image, and sets a single color index as transparent.
    This yields a GIF-compatible frame with 1-bit transparency (fully transparent vs fully opaque).
    """
    # Extract the alpha channel
    alpha = rgba_frame.getchannel('A')

    # Convert RGBA -> RGB -> P with up to 255 colors (so we can reserve index 255 for transparency)
    pal_frame = rgba_frame.convert('RGB').convert('P', palette=Image.ADAPTIVE, colors=255)

    # Use the alpha channel to decide which pixels become fully transparent  
    # If alpha <= 128 => set to palette index 255
    mask = Image.eval(alpha, lambda a: 255 if a <= 128 else 0)

    # Paste palette index 255 into those mask areas
    pal_frame.paste(255, mask)

    # Mark palette index 255 as the transparent index
    pal_frame.info['transparency'] = 255
    return pal_frame

def create_rounded_corners_gif(input_gif, output_gif, corner_radius=30, blur_radius=0):
    """
    Reads an existing GIF, rounds its corners using mask_rounded_corners(),
    and saves a new GIF with 1-bit transparency at the corners.
    The output GIF will have the same dimensions as the original.
    """
    frames = []

    with Image.open(input_gif) as orig_gif:
        # Iterate over each frame in the original GIF
        for frame in ImageSequence.Iterator(orig_gif):
            # Convert to RGBA so we can alter alpha
            rgba_frame = frame.convert("RGBA")

            # Round corners on this frame
            rounded = mask_rounded_corners(rgba_frame, corner_radius=corner_radius, blur_radius=blur_radius)

            # Convert RGBA -> paletted image with single-color transparency
            pal_frame = transparent_indexed_gif_frame(rounded)
            frames.append(pal_frame)

    if frames:
        # Write frames to a new animated GIF
        # optimize=False is recommended for preserving transparency
        frames[0].save(
            output_gif,
            save_all=True,
            append_images=frames[1:],
            loop=0,  # 0 => loop forever
            disposal=2,
            optimize=False
        )
        print(f"Saved rounded-corner GIF to: {output_gif}")
    else:
        print("No frames found in", input_gif)

# -------------------------------------------
# Example usage:
if __name__ == "__main__":
    # 1) Path to original GIF
    input_path = "Templates_Accessing_Templates.gif"
    # 2) Path to output
    output_path = "Templates_Accessing_Templates_Rounded.gif"

    # 3) Corner radius (in pixels). Increase for more rounded corners
    corner_radius = 50
    # 4) Optionally blur the edges some. But remember, you'll only have fully transparent or fully opaque
    blur_radius = 0  

    create_rounded_corners_gif(input_path, output_path, corner_radius, blur_radius)
