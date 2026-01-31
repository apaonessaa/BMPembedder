import math
import AnalyzerException

class Analyzer:
    raw_image: bytearray=[]
    debug: bool=False

    def __init__(self, raw_image, debug):
        self.raw_image = bytearray(raw_image)
        self.debug = debug

    def check_width(self, func, w: int):
        def wrapper(*args, **kargs):
            width, _ = self.get_size()
            if w<0 or w>=width:
                raise AnalyzerException.ValueNotInExcludeEnd("Analyzer",w,0,width)
            res = func(args, kargs)
            return res
        return wrapper

    def check_height(self, func, h: int):
        def wrapper(*args, **kargs):
            _, height = self.get_size()
            if h<0 or h>=height:
                raise AnalyzerException.ValueNotInExcludeEnd("Analyzer",h,0,height)
            res = func(args, kargs)
            return res
        return wrapper

    def check_layer(self, func, layer: int):
        def wrapper(*args, **kargs):
            Bpp = self.get_Bpp()
            if layer >= Bpp:
                raise AnalyzerException.ValueNotInExcludeEnd("Analyzer",layer,0,Bpp)
            res = func(args, kargs)
            return res
        return wrapper

    def check_sublayer(self, func, sublayer: int):
         def wrapper(self, *args, **kargs):
            bpp = self.get_bpp()
            if sublayer >= bpp:
                raise AnalyzerException.ValueNotInExcludeEnd("Analyzer",sublayer,0,bpp)
            res = func(self, args, kargs)
            return res
        return wrapper

    def set_raw_image(self, raw_image):
        self.raw_image = bytearray(raw_image)
            
    def get_raw_image(self):
        return bytes(self.raw_image)

    def get_offset(self):
        # bitmap image data (pixel array) offset
        # [+] start offset:     10 bytes
        # [+] size:             4 bytes
        return int.from_bytes(self.raw_image[10:14], byteorder='little')

    def get_size(self):
        # bitmap image width & height (signed integer)
        # [+] start offset:     18 bytes
        # [+] size:             4 bytes
        width = int.from_bytes(self.raw_image[18:22], byteorder='little')
        height = int.from_bytes(self.raw_image[22:26], byteorder='little')
        return width, height

    def get_bpp(self):
        # bitmap image bpp (bits per pixel)
        # [+] start offset:     28 bytes
        # [+] size:             2 bytes
        bpp = int.from_bytes(self.raw_image[28:30], byteorder='little')
        return bpp
    
    def get_Bpp(self):
        # bitmap image Bpp (Bytes per pixel)
        # Note: 1, 4 o 8 bits per pixel
        bpp = self.get_bpp()
        return max(1, bpp // 8)
    
    def get_rowsize_bpp(self):
        # bitmap image row size in BITS
        # [+] width, image width expressed in pixels
        # [+] bpp, bits per pixel
        width, _ = self.get_size()
        bpp = self.get_bpp()
        return bpp * width
    
    def get_rowsize(self):
        # bitmap image row size in BYTES
        row_size_bpp = self.get_rowsize_bpp()
        return math.ceil(row_size_bpp / 8)

    # Effective rowsize [data + padding]
    def get_eff_rowsize(self):
        return self.get_rowsize() + self.get_padding() 

    def get_payload_size(self):
        # bitmap image size in pixel, pixel array size
        # rawdata + padding
        rowsize = self.get_eff_rowsize() # BYTES
        width, _ = self.get_size()
        return width * rowsize # BYTES
    
    def get_payload(self):
        # bitmap image data (pixel array), bytearray format
        # [+] start offset:     10 bytes
        # [+] size:             4 bytes
        start = self.get_offset()
        payload_size = self.get_payload_size()
        return self.raw_image[start:start+payload_size]
    
    def set_payload(self, payload: bytearray):
        # bitmap image data (pixel array), bytearray format
        # [+] start offset:     10 bytes
        # [+] size:             4 bytes
        start = self.get_offset()
        payload_size = self.get_payload_size()
        if len(payload) != payload_size:
            raise ValueError('Error')
        self.raw_image[start:start+payload_size] = payload
    
    # Padding
    # Bitmap pixel data is stored in rows (also known as strides or scan lines).
    # Each row's size must be a multiple of 4 bytes (a 32-bit DWORD).
    # If the row's raw data is not already a multiple of 4 bytes, padding bytes are added at the end.
    def get_padding(self):  
        # Maximum padding size: 3 bytes (since a full 4-byte padding block is unnecessary).
        #
        # Example: 
        #   - 24-bit BMP (Bpp = 3 bytes per pixel), Width = 1 pixel
        #   - Raw row size = 1 * 3 = 3 bytes (not a multiple of 4)
        #   - (1) Compute remainder: 3 bytes % 4 = 3
        #   - (2) Compute padding: 4 - 3 = 1
        #   - (3) Apply final mod 4 to ensure padding is never 4: (4 - 3) % 4 = 1
        #   - Final row structure: [3 bytes pixel data] + [1 byte padding]
        #
        # General steps:
        #   (1) Compute raw row size: width * Bpp
        #   (2) Compute required padding: 4 - (raw row size % 4)
        #   (3) Apply mod 4 to prevent a full 4-byte padding block (unnecessary)
        #
        # If the row size is already a multiple of 4, the formula ensures padding = 0.
        width, _ = self.get_size()
        Bpp = self.get_Bpp()
        row_padding = (4 - (width * Bpp) % 4)  
        return row_padding % 4 # BYTES
    
    # set LSB raw image to zero
    def clean(self, layer):
        width, height = self.get_size()
        
        for i in range(width):
            for j in range(height):
                self.set_zero(i, j, 0, 0)
        
        if (self.debug):
            print(f"The layer {layer} is cleaned.")
        return self

    # Layers: [ R G B ], Sub-layer: [0 1 2 3 4 5 6 7]
    # Set value to pixel (i,j)
    @check_width(i)
    @check_height(j)
    @check_layer(layer)
    @check_sublayer(sublayer)
    def set_zero(self, i: int, j: int, layer: int, sublayer: int):
        Bpp = self.get_Bpp()
        eff_rowsize = self.get_eff_rowsize()
        offset = i*eff_rowsize + j*Bpp + layer + sublayer # (i*row + j*Bpp) + layer + sublayer
        self.raw_image[offset] &= 0xFE
        return self

