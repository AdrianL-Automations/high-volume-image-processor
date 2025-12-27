import os
import time
from PIL import Image
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import cpu_count
from tqdm import tqdm
import os

# CONFIGURATION
INPUT_DIR = os.getenv('INPUT_DIR', './data/input')
OUTPUT_DIR = os.getenv('OUTPUT_DIR', './data/output')

TARGET_WIDTH = int(os.getenv('TARGET_WIDTH', 800))
TARGET_HEIGHT = int(os.getenv('TARGET_HEIGHT', 800))
TARGET_SIZE = (TARGET_WIDTH, TARGET_HEIGHT)

LOG_FILE = './data/processing_errors.log'

def process_image(filename):
    """
    Resizes a single image. Designed to be run in parallel.
    Preserves PNG transparency, converts others to JPEG.
    """
    try:
        img_path = os.path.join(INPUT_DIR, filename)
        save_path = os.path.join(OUTPUT_DIR, filename)
        
        with Image.open(img_path) as img:
            img = img.resize(TARGET_SIZE, Image.Resampling.LANCZOS)
            
            # Preserve format or convert intelligently
            if img.mode in ("RGBA", "P") and filename.lower().endswith('.png'):
                # Keep PNG for transparency
                img.save(save_path, "PNG", optimize=True)
            else:
                # Convert to JPEG
                if img.mode in ("RGBA", "P", "LA"):
                    img = img.convert("RGB")
                
                # Change extension to .jpg if it was PNG
                if filename.lower().endswith('.png'):
                    save_path = os.path.splitext(save_path)[0] + '.jpg'
                
                img.save(save_path, "JPEG", quality=85, optimize=True)
        
        return (True, f"{filename}")
    except Exception as e:
        return (False, f"{filename}: {str(e)}")

def main():
    # Ensure directories exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    files = [f for f in os.listdir(INPUT_DIR) 
             if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.bmp'))]
    
    if not files:
        print("No images found in data/input!")
        return

    print(f"Starting High-Performance Batch Processing...")
    print(f"CPU Cores Detected: {cpu_count()}")
    print(f"Images to Process: {len(files)}")
    print(f"Target Size: {TARGET_SIZE[0]}x{TARGET_SIZE[1]}")
    print("-" * 50)

    start_time = time.time()

    # THE MAGIC: Parallel Processing using all cores
    with ProcessPoolExecutor(max_workers=cpu_count()) as executor:
        results = list(tqdm(
            executor.map(process_image, files), 
            total=len(files),
            desc="Processing",
            unit="img"
        ))

    end_time = time.time()
    duration = end_time - start_time
    
    # Separate successes and failures
    successes = [r[1] for r in results if r[0]]
    failures = [r[1] for r in results if not r[0]]
    
    # Log errors to file if any
    if failures:
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            f.write(f"Processing Errors - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n")
            for error in failures:
                f.write(error + "\n")
        print(f"\n {len(failures)} errors logged to: {LOG_FILE}")
    
    print("-" * 50)
    print(f"DONE! Processed {len(successes)}/{len(files)} images in {duration:.2f} seconds.")
    
    if duration > 0:
        print(f"Average Speed: {len(successes)/duration:.1f} images/second")
    
    if failures:
        print(f"Failed: {len(failures)} images")
    else:
        print("All images processed successfully!")

if __name__ == '__main__':
    main()


