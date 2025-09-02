jetzt möchte ich ein zweites skript programmieren welches nach dem prepare_images.py aufgerufen wird und die resized bilder mittels dem florence2-modell (GPU beschleunigt) einer captions datei erstellt die genauso heisst wie das bild, bloss mit der endung .txt. bitte achte darauf das du alle befehler im terminal in der venv umgebung machst. es sollen ausserdem keine neuen yaml oder readme-dateien erstellt werden, sondern die vorhandenen erweitert. wenn du florence2 installierst, achte darauf das du nur die GPU-beschleunigten pakete installierst weil sonst florence2 nicht funktioniert.


# LORA Training Image Preparation & Captioning

This project provides scripts to prepare image files for training LoRA models. It includes scaling images and generating detailed captions.

## Features

- **Image Scaling**: Scales images to multiple defined sizes (e.g., 512x512, 1024x1024).
- **Caption Generation**: Generates detailed captions for images using the `Florence-2-large-no-flash-attn` model (modified version without flash_attn dependency).
- Maintains aspect ratio and adds white padding for square output.
- Supports various image formats (JPG, PNG, BMP, TIFF, WEBP).
- Configurable quality settings.
- Automatic directory creation.
- Progress display and detailed logging.
- Skips already existing files (optional).

## Installation

1.  Make sure Python 3.7+ is installed.
2.  It is recommended to use a virtual environment.

    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```
3.  Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```
    For GPU support, ensure you have a compatible PyTorch version installed with CUDA.

## Usage

### 1. Prepare Images

Run the `prepare_images.py` script to scale your images.

```bash
python prepare_images.py
```

### 2. Generate Captions

After preparing the images, run `generate_captions.py` to create text captions for each image.

```bash
# Generate captions for a specific directory
python generate_captions.py datasets/aigarasch/512x512

# Generate captions for 1024x1024 images
python generate_captions.py datasets/aigarasch/1024x1024

# Use custom config and debug logging
python generate_captions.py datasets/mymodel/512x512 --config custom_config.yaml --log-level DEBUG
```

This will process the images in the specified directory and save a `.txt` file for each image with the generated caption.

## Configuration

Edit the `config.yaml` file according to your needs:

```yaml
# Target sizes (square)
target_sizes:
  - 512
  - 1024

# Supported image formats
supported_formats:
  - ".jpg"
  - ".jpeg"
  - ".png"
  - ".bmp"
  - ".tiff"
  - ".webp"

# Quality settings
quality:
  png_compress_level: 1  # 1 = best quality, 9 = smallest size

# Resampling algorithm for best quality
resampling_method: "LANCZOS"

# Overwrite existing files
overwrite_existing: false

# Caption generation settings
caption:
  # Florence-2 prompt for caption generation
  # Available prompts:
  # - "<CAPTION>" - Basic caption
  # - "<DETAILED_CAPTION>" - More detailed description  
  # - "<MORE_DETAILED_CAPTION>" - Very detailed description
  # - "<OD>" - Object detection (lists objects)
  # - "<DENSE_REGION_CAPTION>" - Dense region captions
  prompt: "<MORE_DETAILED_CAPTION>"
  
  # Model settings
  model_id: "microsoft/Florence-2-large"  # or "microsoft/Florence-2-base" for faster processing
  max_new_tokens: 1024
  do_sample: false
  use_cache: false
```

## Usage

The script requires the input directory as a command-line argument. The output directory is automatically derived from the input directory path.

### Basic usage
```bash
python prepare_images.py <input_directory>
```

### Examples

```bash
# Process images from the aigarasch dataset
python prepare_images.py datasets/aigarasch/_raw

# Process images from a custom dataset
python prepare_images.py datasets/mymodel/_raw

# Use a custom configuration file
python prepare_images.py datasets/aigarasch/_raw --config custom_config.yaml

# Enable debug logging
python prepare_images.py datasets/aigarasch/_raw --log-level DEBUG
```

### Command Line Options

- `input_directory` (required): Path to directory containing source images
- `--config, -c`: Configuration file path (default: config.yaml)
- `--log-level`: Logging level (DEBUG, INFO, WARNING, ERROR, default: INFO)

### Directory Structure

The script automatically derives the output directory from the input directory:

- Input: `datasets/mymodel/_raw` → Output: `datasets/mymodel/`
- Input: `path/to/images/_raw` → Output: `path/to/images/`
- Input: `datasets/custom` → Output: `datasets/custom/`

## Output Structure

The script creates the following directory structure:

```
datasets/aigarasch/
├── 512x512/
│   ├── image001.png
│   ├── image002.png
│   └── ...
└── 1024x1024/
    ├── image001.png
    ├── image002.png
    └── ...
```

After running `generate_captions.py`, you will also have `.txt` files:
```
datasets/aigarasch/
├── 512x512/
│   ├── image001.png
│   ├── image001.txt
│   ├── image002.png
│   ├── image002.txt
│   └── ...
└── 1024x1024/
    ├── image001.png
    ├── image001.txt
    ├── image002.png
    ├── image002.txt
    └── ...
```

## Image Processing

- **Aspect ratio**: Maintained, smaller side is scaled to target size
- **Padding**: White background is added for square output
- **Format**: All output images are saved as PNG with optimal quality
- **Quality**: Low compression level (1) for best results

## Example

For your existing images in `datasets/aigarasch/_raw/`:

```bash
python prepare_images.py
python generate_captions.py
```

This will first process all PNG files and create scaled versions in:
- `datasets/aigarasch/512x512/`
- `datasets/aigarasch/1024x1024/`

Then, it will generate captions for each of the scaled images.

## Supported Resampling Methods

- `NEAREST` - Fast, low quality
- `BILINEAR` - Medium
- `BICUBIC` - Good
- `LANCZOS` - Best quality (recommended)
- `HAMMING` - Good for downscaling
- `BOX` - Good for downscaling

## Tips

1. **Large datasets**: Use `--log-level WARNING` for less output
2. **Quality vs. size**: Increase `png_compress_level` for smaller files (1=best quality, 9=smallest)
3. **Batch processing**: The script can be safely interrupted and resumed
4. **Storage space**: Consider that multiple copies of images will be created
