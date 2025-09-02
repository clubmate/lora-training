#!/usr/bin/env python3
"""
LORA Training Caption Generation Script

This script generates captions for images using the Florence-2 model.
"""

import os
import sys
import yaml
import argparse
from pathlib import Path
from PIL import Image
import torch
from transformers import AutoProcessor, AutoModelForCausalLM
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
            return yaml.safe_load(file)
    except FileNotFoundError:
        logging.error(f"Configuration file not found: {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logging.error(f"Error loading configuration: {e}")
        sys.exit(1)

def get_image_files(directory: Path, supported_formats: List[str]) -> List[Path]:
    """Get all image files from a directory."""
    image_files = []
    for fmt in supported_formats:
        image_files.extend(directory.glob(f"*{fmt}"))
    return image_files

def generate_caption(model, processor, image_path: Path, device: str) -> str:
    """Generates a caption for a single image using Florence-2."""
    try:
        image = Image.open(image_path).convert("RGB")
        
        # Florence-2 captioning prompt
        prompt = "<MORE_DETAILED_CAPTION>"
        
        # Determine torch_dtype
        torch_dtype = torch.float16 if device == "cuda" else torch.float32
        
        # Process the image
        inputs = processor(text=prompt, images=image, return_tensors="pt")
        
        # Move inputs to device with proper dtype - check for None first
        inputs_to_device = {}
        for k, v in inputs.items():
            if v is not None:
                if hasattr(v, 'dtype') and v.dtype.is_floating_point:
                    inputs_to_device[k] = v.to(device, torch_dtype)
                else:
                    inputs_to_device[k] = v.to(device)
            else:
                inputs_to_device[k] = v
        
        # Generate caption - use simple greedy search to avoid beam search issues
        generated_ids = model.generate(
            input_ids=inputs_to_device["input_ids"],
            pixel_values=inputs_to_device["pixel_values"],
            max_new_tokens=1024,
            do_sample=False,
            use_cache=False  # Disable cache to avoid past_key_values issues
        )
        
        # Decode the generated text
        generated_text = processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
        
        # Parse the output using Florence-2's post-processing
        parsed_answer = processor.post_process_generation(
            generated_text, 
            task=prompt, 
            image_size=(image.width, image.height)
        )
        
        # Extract the caption text
        caption = parsed_answer.get(prompt, "")
        if isinstance(caption, str):
            return caption.strip()
        elif isinstance(caption, list) and len(caption) > 0:
            return caption[0].strip()
        else:
            return "Unable to generate caption"
            
    except Exception as e:
        logging.error(f"Error in generate_caption: {e}")
        return f"Error: {str(e)}"

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Generate captions for LORA training images.")
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to the configuration file.",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level.",
    )
    args = parser.parse_args()
    setup_logging(args.log_level)

    config = load_config(args.config)
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logging.info(f"Using device: {device}")

    # Load Florence-2 model (use base version which is more stable)
    model_id = 'microsoft/Florence-2-large'
    logging.info(f"Loading Florence-2 model: {model_id}")
    
    # Determine torch_dtype
    torch_dtype = torch.float16 if device == "cuda" else torch.float32
    
    processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch_dtype,
        trust_remote_code=True,
        device_map="auto" if device == "cuda" else None,
        attn_implementation="eager"  # Force eager attention to avoid SDPA issues
    ).to(device)
    
    if device != "cuda":
        model = model.to(device)

    datasets_base_dir = Path("datasets")
    target_sizes = config.get("target_sizes", [])
    supported_formats = config.get("supported_formats", [])

    for dataset_dir in datasets_base_dir.iterdir():
        if not dataset_dir.is_dir() or dataset_dir.name.endswith("_raw"):
            continue
        
        for size in target_sizes:
            size_dir = dataset_dir / f"{size}x{size}"
            if not size_dir.exists():
                continue

            logging.info(f"Processing directory: {size_dir}")
            image_files = get_image_files(size_dir, supported_formats)
            
            for image_path in image_files:
                caption_path = image_path.with_suffix(".txt")
                if caption_path.exists():
                    logging.info(f"Caption already exists for {image_path.name}, skipping.")
                    continue

                logging.info(f"Generating caption for {image_path.name}...")
                try:
                    caption = generate_caption(model, processor, image_path, device)
                    with open(caption_path, "w", encoding="utf-8") as f:
                        f.write(caption)
                    logging.info(f"  -> Saved caption to {caption_path.name}")
                except Exception as e:
                    logging.error(f"Failed to generate caption for {image_path.name}: {e}")

if __name__ == "__main__":
    main()
