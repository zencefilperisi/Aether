# utility/stego.py
from PIL import Image
import binascii

class AetherStego:
    """
    LSB (Least Significant Bit) Steganography
    Hides data in image pixels securely.
    """
    def encode_image(self, input_image_path, secret_data, output_image_path):
        img = Image.open(input_image_path)
        binary_data = bin(int(binascii.hexlify(secret_data.encode()), 16))[2:].zfill(8 * len(secret_data))
        binary_data += '1111111111111110'  # EOF marker

        pixels = list(img.getdata())
        new_pixels = []
        data_index = 0

        for pixel in pixels:
            # Handle RGBA or RGB
            rgb_pixel = pixel[:3] if len(pixel) >= 3 else pixel
            new_pixel = list(rgb_pixel)
            for i in range(len(new_pixel)):
                if data_index < len(binary_data):
                    new_pixel[i] = (new_pixel[i] & ~1) | int(binary_data[data_index])
                    data_index += 1
            # Preserve original tuple length (e.g., add alpha back if present)
            if len(pixel) == 4:
                new_pixel.append(pixel[3])
            new_pixels.append(tuple(new_pixel))

        img.putdata(new_pixels)
        img.save(output_image_path, "PNG")
        return True

    def decode_image(self, image_path):
        img = Image.open(image_path)
        pixels = list(img.getdata())
        binary_data = ""

        for pixel in pixels:
            rgb_pixel = pixel[:3] if len(pixel) >= 3 else pixel
            for channel in rgb_pixel:
                binary_data += str(channel & 1)

        eof_index = binary_data.find('1111111111111110')
        if eof_index != -1:
            binary_data = binary_data[:eof_index]
            
        byte_data = int(binary_data, 2).to_bytes((len(binary_data) + 7) // 8, byteorder='big')
        return byte_data.decode(errors='ignore')