# LORA Training Image Preparation

This script prepares image files for training LoRA models by scaling them to different target sizes and organizing them into corresponding directories.

## Features

- Scales images to multiple defined sizes (e.g., 512x512, 1024x1024)
- Maintains aspect ratio and adds white padding for square output
- Supports various image formats (JPG, PNG, BMP, TIFF, WEBP)
- Configurable quality settings
- Automatic directory creation
- Progress display and detailed logging
- Skips already existing files (optional)

## Installation

1. Make sure Python 3.7+ is installed
2. Install dependencies:

```bash
pip install -r requirements.txt
```

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

## Image Processing

- **Aspect ratio**: Maintained, smaller side is scaled to target size
- **Padding**: White background is added for square output
- **Format**: All output images are saved as PNG with optimal quality
- **Quality**: Low compression level (1) for best results

## Example

For your existing images in `datasets/aigarasch/_raw/`:

```bash
python prepare_images.py
```

This will process all PNG files and create scaled versions in:
- `datasets/aigarasch/512x512/`
- `datasets/aigarasch/1024x1024/`

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
