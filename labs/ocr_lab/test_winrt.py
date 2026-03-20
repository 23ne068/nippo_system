import asyncio
import cv2
import numpy as np

try:
    from winsdk.windows.media.ocr import OcrEngine
    from winsdk.windows.globalization import Language
    from winsdk.windows.graphics.imaging import SoftwareBitmap, BitmapPixelFormat, BitmapAlphaMode
    USE_WINSDK = True
except ImportError:
    USE_WINSDK = False

async def run_ocr_winrt(image_numpy):
    if not USE_WINSDK:
        print("Error: winsdk is not installed")
        return
    
    lang = Language("ja-JP")
    if not OcrEngine.is_language_supported(lang):
        print("Error: Japanese OCR not supported by Windows. Please install Japanese Language Pack.")
        # Fallback to English to test at least
        lang = Language("en-US")
        if not OcrEngine.is_language_supported(lang):
            return
            
    engine = OcrEngine.try_create_from_language(lang)
    
    # Convert numpy BGR to RGBA for WinRT
    image_rgba = cv2.cvtColor(image_numpy, cv2.COLOR_BGR2RGBA)
    height, width, _ = image_rgba.shape
    
    # Create SoftwareBitmap
    bmp = SoftwareBitmap(BitmapPixelFormat.RGBA8, width, height, BitmapAlphaMode.PREMULTIPLIED)
    
    # For winsdk, copy_pixels_from_buffer expects a memoryview/buffer
    bmp.copy_from_buffer(memoryview(image_rgba.tobytes()))
    
    result = await engine.recognize_async(bmp)
    
    print(f"Total lines found: {len(result.lines)}")
    for i, line in enumerate(result.lines):
        print(f"Line {i}: {line.text}")

if __name__ == "__main__":
    img = np.zeros((200, 500, 3), dtype=np.uint8)
    img.fill(255)
    cv2.putText(img, "Hello Windows Media OCR Test!", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    
    asyncio.run(run_ocr_winrt(img))
