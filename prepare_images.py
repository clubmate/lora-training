#!/usr/bin/env python3
"""
LORA Training Image Preparation Script

This script scales images from an input directory to various
target sizes and saves them to corresponding output directories.
"""

import os
import sys
import yaml
import argparse
from pathlib import Path
from PIL import Image, ImageOps
import logging
from typing import List, Dict, Any


def setup_logging(log_level: str = "INFO") -> None:
    """Sets up logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(message)s'
    )


def load_config(config_path: str) -> Dict[str, Any]:
    """Loads configuration from a YAML file."""
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        logging.info(f"Configuration loaded: {config_path}")
        return config
    except FileNotFoundError:
        logging.error(f"Configuration file not found: {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logging.error(f"Error loading configuration: {e}")
        sys.exit(1)


def get_resampling_method(method_name: str):
    """Returns the corresponding PIL resampling method."""
    methods = {
        "NEAREST": Image.NEAREST,
        "BILINEAR": Image.BILINEAR,
        "BICUBIC": Image.BICUBIC,
        "LANCZOS": Image.LANCZOS,
        "HAMMING": Image.HAMMING,
        "BOX": Image.BOX
    }
    return methods.get(method_name.upper(), Image.LANCZOS)


def get_image_files(directory: str, supported_formats: List[str]) -> List[Path]:
    """Finds all supported image files in the directory."""
    directory_path = Path(directory)
    if not directory_path.exists():
        logging.error(f"Input directory does not exist: {directory}")
        return []
    
    image_files = []
    for ext in supported_formats:
        # Search for lowercase extension
        pattern = f"*{ext.lower()}"
        image_files.extend(directory_path.glob(pattern))
        # Also consider uppercase variants only if different from lowercase
        upper_pattern = f"*{ext.upper()}"
        if upper_pattern != pattern:
            image_files.extend(directory_path.glob(upper_pattern))
    
    # Remove duplicates by converting to set and back to list
    unique_files = list(set(image_files))
    
    logging.info(f"Found image files: {len(unique_files)}")
    return sorted(unique_files)


def create_output_directories(base_dir: str, sizes: List[int]) -> Dict[int, Path]:
    """Creates output directories for each target size."""
    output_dirs = {}
    base_path = Path(base_dir)
    
    for size in sizes:
        size_dir = base_path / f"{size}x{size}"
        size_dir.mkdir(parents=True, exist_ok=True)
        output_dirs[size] = size_dir
        logging.info(f"Output directory created: {size_dir}")
    
    return output_dirs


def resize_image(image_path: Path, target_size: int, resampling_method) -> Image.Image:
    """
    Scales an image to the target size (square) while maintaining aspect ratio.
    Adds padding if necessary to achieve square format.
    """
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary (for JPEG output)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create white background for transparent images
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Calculate scaling factor to fit the image within target_size
            original_width, original_height = img.size
            scale_factor = min(target_size / original_width, target_size / original_height)
            
            # Calculate new dimensions
            new_width = int(original_width * scale_factor)
            new_height = int(original_height * scale_factor)
            
            # Resize the image (both up and down scaling)
            img = img.resize((new_width, new_height), resampling_method)
            
            # Create square image with white background
            square_img = Image.new('RGB', (target_size, target_size), (255, 255, 255))
            
            # Center the image
            offset_x = (target_size - img.width) // 2
            offset_y = (target_size - img.height) // 2
            square_img.paste(img, (offset_x, offset_y))
            
            return square_img
            
    except Exception as e:
        logging.error(f"Error opening/processing {image_path}: {e}")
        return None


def save_image(image: Image.Image, output_path: Path, quality_settings: Dict[str, Any]) -> bool:
    """Saves the image with the specified quality settings."""
    try:
        # Always save as PNG with optimal quality
        image.save(
            output_path,
            'PNG',
            compress_level=quality_settings.get('png_compress_level', 6),
            optimize=True
        )
        
        return True
    except Exception as e:
        logging.error(f"Error saving {output_path}: {e}")
        return False


def process_images(config: Dict[str, Any], input_dir: str) -> None:
    """Main function for processing all images."""
    # Input directory is now required from CLI
    input_directory = input_dir
    
    # Generate output base directory from input directory
    # Remove '_raw' suffix if present and use parent directory
    input_path = Path(input_directory)
    if input_path.name == "_raw":
        output_base = str(input_path.parent)
    else:
        output_base = str(input_path.parent / input_path.name.replace("_raw", ""))
    
    # Get all required configuration parameters
    target_sizes = config['target_sizes']
    supported_formats = config['supported_formats']
    quality_settings = config['quality']
    resampling_method = get_resampling_method(config['resampling_method'])
    overwrite_existing = config.get('overwrite_existing', False)
    
    logging.info(f"Input directory: {input_directory}")
    logging.info(f"Output base directory: {output_base}")
    
    # Find all image files
    image_files = get_image_files(input_directory, supported_formats)
    if not image_files:
        logging.warning("No image files found!")
        return
    
    # Create output directories
    output_dirs = create_output_directories(output_base, target_sizes)
    
    # Statistics
    total_files = len(image_files)
    processed_count = 0
    error_count = 0
    
    logging.info(f"Starting processing of {total_files} images...")
    
    for i, image_path in enumerate(image_files, 1):
        logging.info(f"Processing ({i}/{total_files}): {image_path.name}")
        
        # Process for each target size
        image_processed = False
        
        for target_size in target_sizes:
            output_dir = output_dirs[target_size]
            output_path = output_dir / f"{image_path.stem}.png"  # Always save as PNG
            
            # Check if file already exists
            if output_path.exists() and not overwrite_existing:
                logging.info(f"Skipping {output_path} (already exists)")
                continue
            
            # Resize the image
            resized_image = resize_image(image_path, target_size, resampling_method)
            if resized_image is None:
                error_count += 1
                continue
            
            # Save the image
            if save_image(resized_image, output_path, quality_settings):
                logging.debug(f"Saved: {output_path}")
                image_processed = True
            else:
                error_count += 1
        
        if image_processed:
            processed_count += 1
    
    # Summary
    logging.info(f"\nProcessing completed!")
    logging.info(f"Successfully processed: {processed_count}/{total_files}")
    if error_count > 0:
        logging.warning(f"Errors occurred: {error_count}")
    
    # Show output directories
    for size, dir_path in output_dirs.items():
        file_count = len(list(dir_path.glob("*.png")))
        logging.info(f"Directory {size}x{size}: {file_count} files")


def main():
    """Main function of the script."""
    parser = argparse.ArgumentParser(
        description="Prepares images for LORA training",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python prepare_images.py datasets/aigarasch/_raw
  python prepare_images.py datasets/mymodel/_raw
  python prepare_images.py /path/to/images/_raw --config custom_config.yaml
  python prepare_images.py datasets/aigarasch/_raw --log-level DEBUG
  
The script automatically derives the output directory from the input directory.
For input 'datasets/mymodel/_raw', output will be 'datasets/mymodel/'.
        """
    )
    
    parser.add_argument(
        'input_directory',
        help='Path to the directory containing source images (required)'
    )
    
    parser.add_argument(
        '-c', '--config',
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Log level (default: INFO)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Check if input directory exists
    if not os.path.exists(args.input_directory):
        logging.error(f"Input directory does not exist: {args.input_directory}")
        sys.exit(1)
    
    # Load configuration
    try:
        config = load_config(args.config)
        logging.info(f"Configuration loaded from: {args.config}")
    except Exception as e:
        logging.error(f"Error loading configuration: {e}")
        sys.exit(1)
    
    # Start processing
    try:
        process_images(config, args.input_directory)
        logging.info("Image processing completed successfully!")
    except KeyboardInterrupt:
        logging.info("\nProcessing interrupted by user.")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
