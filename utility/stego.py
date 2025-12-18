from PIL import Image
import binascii

class AetherStego:
    """
    LSB (Least Significant Bit) Steganography
    Veriyi görsellerin piksellerine kaotik olmayan ama güvenli bir yöntemle gizler.
    """
    def encode_image(self, input_image_path, secret_data, output_image_path):
        img = Image.open(input_image_path)
        binary_data = bin(int(binascii.hexlify(secret_data.encode()), 16))[2:].zfill(8 * len(secret_data))
        binary_data += '1111111111111110' # Bitirme işareti (EOF)

        pixels = list(img.getdata())
        new_pixels = []
        data_index = 0

        for pixel in pixels:
            new_pixel = list(pixel)
            for i in range(3): # R, G, B kanalları
                if data_index < len(binary_data):
                    # En önemsiz biti değiştir (LSB)
                    new_pixel[i] = new_pixel[i] & ~1 | int(binary_data[data_index])
                    data_index += 1
            new_pixels.append(tuple(new_pixel))

        img.putdata(new_pixels)
        img.save(output_image_path, "PNG")
        return True

    def decode_image(self, image_path):
        img = Image.open(image_path)
        pixels = list(img.getdata())
        binary_data = ""

        for pixel in pixels:
            for i in range(3):
                binary_data += str(pixel[i] & 1)

        # Bitirme işaretini bul
        eof_index = binary_data.find('1111111111111110')
        if eof_index != -1:
            binary_data = binary_data[:eof_index]
            
        byte_data = int(binary_data, 2).to_bytes((len(binary_data) + 7) // 8, byteorder='big')
        return byte_data.decode(errors='ignore')