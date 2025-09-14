# Image Comparator with ELO Rating

A Python GUI application for comparing images and ranking them using an ELO rating system.

## Features

- **Side-by-side image comparison** with clickable interface
- **ELO rating system** for fair and accurate image rankings
- **Smart pair selection** that avoids repeating the same comparisons
- **Comprehensive rankings view** with thumbnails and statistics
- **Keyboard shortcuts** for efficient navigation
- **Export/Import functionality** to save and restore rankings
- **Support for multiple image formats** (JPG, PNG, BMP, GIF, TIFF, WebP)

## Requirements

- Python 3.7+
- Pillow (PIL)

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements_image_comparator.txt
```

2. Run the application:
```bash
python image_comparator.py
```

## Usage

### Basic Workflow

1. **Select Directory**: Click "Browse" or press Ctrl+O to select a folder containing images
2. **Compare Images**: Two random images will appear side by side
3. **Choose Winner**: Click on the better image or use arrow keys (← for left, → for right)
4. **View Rankings**: Click "Rankings" to see all images sorted by their ELO scores

### Keyboard Shortcuts

- `←` (Left Arrow) - Left image wins
- `→` (Right Arrow) - Right image wins
- `Space` - Skip this pair
- `Ctrl+O` - Open directory
- `F1` - Show help
- `Esc` - Exit application

### Features

**ELO Rating System**: 
- All images start with a rating of 1500
- Winning against higher-rated images gives more points
- Losing against lower-rated images costs more points
- The system converges to accurate rankings over time

**Smart Pair Selection**:
- Automatically avoids showing the same pair repeatedly
- Prioritizes comparisons between images that haven't been compared
- Ensures fair distribution of comparisons

**Rankings View**:
- Shows all images sorted by ELO rating
- Displays thumbnails, filenames, and comparison counts
- Color-coded ratings (green = above average, red = below average)
- Resizable panels with mouse drag functionality
- Full-size image preview on click

**Data Persistence**:
- Export rankings to JSON format for backup
- Import previous rankings to continue sessions
- Automatically tracks comparison history

## Tips for Best Results

1. **Compare consistently**: Try to use similar criteria for all comparisons
2. **Make enough comparisons**: More comparisons lead to more accurate rankings
3. **Mixed comparisons**: The algorithm works best when images compete across different skill levels
4. **Save progress**: Export your rankings regularly to avoid losing progress

## Technical Details

**ELO Algorithm**: Uses a K-factor of 32, which provides good responsiveness to new comparisons while maintaining stability.

**Image Loading**: Automatically handles different image formats and aspect ratios. Images are displayed at original size in comparison view for fastest loading, with thumbnails used only in rankings list.

**Performance**: Designed to handle hundreds of images efficiently. For very large datasets (1000+ images), the smart pair selection limits sampling to maintain responsiveness.

## Troubleshooting

**Images not loading**: Ensure your directory contains supported image formats (JPG, PNG, BMP, GIF, TIFF, WebP).

**Keyboard shortcuts not working**: Click on the main window to ensure it has focus.

**Performance issues**: For very large image collections, consider organizing into smaller subdirectories.

## Example Use Cases

- **Photography**: Compare and rank your best photos
- **Art Selection**: Choose the best artwork or designs
- **Dataset Curation**: Rank images in machine learning datasets
- **Content Selection**: Choose the best images for websites or presentations

---

# LORA Training Image Preparation & Captioning

This project also provides scripts to prepare image files for training LoRA models. It includes scaling images and generating detailed captions.

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
  
  # Text processing settings
  remove_phrases:
    - "The image shows"
    - "The image is"
    - "This image shows"
    - "This image is"
    - "The picture shows"
    - "The picture is"
    # Add more phrases you want to remove from the beginning of captions
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
